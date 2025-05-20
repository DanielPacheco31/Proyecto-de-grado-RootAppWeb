"""Vistas para la aplicación de pagos."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from facturas.models import Factura
from facturas.utils import generar_factura

from .models import Compra, MetodoPago, Pago
from .tasks import enviar_correo_confirmacion


def inicializar_metodos_pago() -> int:
    """Función auxiliar para inicializar los métodos de pago predeterminados.

    Puedes llamar a esta función manualmente o desde una vista.

    Returns:
        int: Número de métodos de pago inicializados.

    """
    metodos_pago = [
        {
            "tipo": "nequi",
            "nombre": "Nequi",
            "activo": True,
            "configuracion": {"descripcion": "Pago móvil rápido y seguro"},
        },
        {
            "tipo": "bancolombia",
            "nombre": "Bancolombia",
            "activo": True,
            "configuracion": {"descripcion": "Transferencia bancaria"},
        },
        {
            "tipo": "pse",
            "nombre": "PSE",
            "activo": True,
            "configuracion": {"descripcion": "Pago seguro electrónico"},
        },
        {
            "tipo": "tarjeta",
            "nombre": "Tarjeta de Crédito",
            "activo": True,
            "configuracion": {"descripcion": "Visa, MasterCard, American Express"},
        },
    ]

    for metodo in metodos_pago:
        MetodoPago.objects.get_or_create(
            tipo=metodo["tipo"],
            defaults={
                "nombre": metodo["nombre"],
                "activo": metodo["activo"],
                "configuracion": metodo["configuracion"],
            },
        )

    return len(metodos_pago)


# Función auxiliar para reducir la complejidad de procesar_pago
def _verificar_pago_existente(
    request: HttpRequest, compra: Compra,
) -> HttpResponse | None:
    """Verifica si ya existe un pago para la compra y redirige según corresponda.

    Args:
        request: La solicitud HTTP.
        compra: Objeto Compra a verificar.

    Returns:
        HttpResponse o None: Redirección si existe un pago, None si no.

    """
    try:
        pago_existente = Pago.objects.get(compra=compra)
        # Si ya existe, redirigir según el tipo de método de pago
        if pago_existente.metodo_pago.tipo == "nequi":
            messages.info(request, "Ya existe un pago en proceso para esta compra")
            return redirect("pagos:pago_movil", pago_id=pago_existente.id)
        if pago_existente.metodo_pago.tipo == "bancolombia":
            messages.info(request, "Ya existe un pago en proceso para esta compra")
            return redirect("pagos:pago_transferencia", pago_id=pago_existente.id)
        messages.info(request, "Ya existe un pago en proceso para esta compra")
        return redirect("pagos:confirmar_pago", pago_id=pago_existente.id)
    except Pago.DoesNotExist:
        # Si no existe, continuamos con el proceso normal
        return None


def _obtener_metodo_pago(metodo_pago_id: str) -> MetodoPago | None:
    """Obtiene el método de pago basado en el ID proporcionado.

    Args:
        metodo_pago_id: ID del método de pago desde el formulario.

    Returns:
        MetodoPago o None: Instancia del método de pago o None si hay error.

    """
    try:
        # Si es un ID numérico válido de la base de datos
        metodo_id = int(metodo_pago_id)
        try:
            return MetodoPago.objects.get(id=metodo_id, activo=True)
        except MetodoPago.DoesNotExist:
            # Si no existe en la BD, usar el mapeo de IDs de la interfaz
            tipo_metodo = _get_tipo_metodo_por_id_frontend(metodo_pago_id)
            return _obtener_o_crear_metodo_pago(tipo_metodo)
    except (ValueError, TypeError):
        # Si no es un ID numérico, usar el mapeo de IDs de la interfaz
        tipo_metodo = _get_tipo_metodo_por_id_frontend(metodo_pago_id)
        return _obtener_o_crear_metodo_pago(tipo_metodo)


def _crear_pago(compra: Compra, metodo_pago: MetodoPago) -> tuple[Pago | None, str]:
    """Crea un registro de pago para la compra.

    Args:
        compra: Objeto Compra a pagar.
        metodo_pago: Método de pago a utilizar.

    Returns:
        tuple: (Pago creado o None, mensaje de error o cadena vacía)

    """
    try:
        pago = Pago.objects.create(
            compra=compra,
            metodo_pago=metodo_pago,
            monto=compra.total,
            estado="pendiente",
        )
    except (ValueError, TypeError, Pago.DoesNotExist, MetodoPago.DoesNotExist) as e:
        # Reemplazamos Exception por excepciones específicas
        return None, f"Error al procesar el pago: {e!s}"
    else:
        # Este bloque se ejecuta cuando no hay excepciones
        return pago, ""


def _redirigir_segun_metodo_pago(
    request: HttpRequest, metodo_pago: MetodoPago, pago: Pago, compra_id: int,
) -> HttpResponse:
    """Redirige según el método de pago seleccionado.

    Args:
        request: La solicitud HTTP.
        metodo_pago: Método de pago seleccionado.
        pago: Pago creado.
        compra_id: ID de la compra.

    Returns:
        HttpResponse: Redirección a la página correspondiente.

    """
    if metodo_pago.tipo == "nequi":
        return redirect("pagos:pago_movil", pago_id=pago.id)
    if metodo_pago.tipo == "bancolombia":
        return redirect("pagos:pago_transferencia", pago_id=pago.id)
    if metodo_pago.tipo in {"pse", "tarjeta"}:
        messages.error(request, "Este método de pago aún no está implementado")
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra_id)

    messages.error(request, f"Método de pago no válido: {metodo_pago.tipo}")
    return redirect("pagos:seleccionar_metodo_pago", compra_id=compra_id)


@login_required
def seleccionar_metodo_pago(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Permite al usuario seleccionar un método de pago para su compra.

    Args:
        request: La solicitud HTTP.
        compra_id: ID de la compra a pagar.

    Returns:
        HttpResponse: Página de selección de método de pago o redirección.

    """
    # Asegurarse de que existan los métodos de pago
    if MetodoPago.objects.count() == 0:
        inicializar_metodos_pago()

    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    # Si la compra ya está pagada, redirigir al detalle
    if compra.estado != "pendiente":
        messages.info(request, "Esta compra ya ha sido procesada")
        return redirect("facturas:detalle_compra", compra_id=compra.id)

    # Métodos de pago disponibles
    metodos_pago = MetodoPago.objects.filter(activo=True)

    return render(request, "pagos/metodoDepago.html", {
        "compra": compra,
        "metodos_pago": metodos_pago,
    })


@login_required
def procesar_pago(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Procesa el pago de una compra según el método seleccionado.

    Args:
        request: La solicitud HTTP.
        compra_id: ID de la compra a procesar.

    Returns:
        HttpResponse: Redirección según el método de pago seleccionado.

    """
    if request.method != "POST":
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra_id)

    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    # Si la compra ya está pagada, redirigir al detalle
    if compra.estado != "pendiente":
        messages.info(request, "Esta compra ya ha sido procesada")
        return redirect("facturas:detalle_compra", compra_id=compra.id)

    # Verificar si ya existe un Pago para esta compra
    redirect_response = _verificar_pago_existente(request, compra)
    if redirect_response:
        return redirect_response

    # Combinamos tres condiciones de error con una sola redirección
    metodo_pago_id = request.POST.get("metodo_pago")
    if not metodo_pago_id:
        messages.error(request, "Debes seleccionar un método de pago")
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)

    # Obtener método de pago y crear registro de pago
    metodo_pago = _obtener_metodo_pago(metodo_pago_id)
    if not metodo_pago:
        messages.error(request, "Método de pago no encontrado")
    else:
        # Crear el registro de pago
        pago, error = _crear_pago(compra, metodo_pago)
        if not error:
            # Redirigir según el método de pago
            return _redirigir_segun_metodo_pago(request, metodo_pago, pago, compra_id)
        messages.error(request, error)

    # Si llegamos aquí es porque hubo algún error en el método de pago o la creación
    return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)


def _get_tipo_metodo_por_id_frontend(id_frontend: str) -> str:
    """Mapea los IDs del frontend a tipos de método de pago.

    Args:
        id_frontend: ID del método de pago en el frontend.

    Returns:
        str: Tipo de método de pago correspondiente.

    """
    mapa_ids = {
        "1": "nequi",
        "2": "bancolombia",
        "3": "pse",
        "4": "tarjeta",
    }
    return mapa_ids.get(id_frontend, "bancolombia")  # Por defecto bancolombia


def _obtener_o_crear_metodo_pago(tipo_metodo: str) -> MetodoPago:
    """Obtiene o crea un método de pago por tipo.

    Args:
        tipo_metodo: Tipo de método de pago.

    Returns:
        MetodoPago: Instancia del método de pago.

    """
    nombres = {
        "nequi": "Nequi",
        "bancolombia": "Bancolombia",
        "pse": "PSE",
        "tarjeta": "Tarjeta de Crédito",
    }

    metodo_pago, _ = MetodoPago.objects.get_or_create(
        tipo=tipo_metodo,
        defaults={
            "nombre": nombres.get(tipo_metodo, tipo_metodo.capitalize()),
            "activo": True,
        },
    )
    return metodo_pago


@login_required
def pago_transferencia(request: HttpRequest, pago_id: int) -> HttpResponse:
    """Gestiona el proceso de pago mediante transferencia bancaria.

    Args:
        request: La solicitud HTTP.
        pago_id: ID del pago a procesar.

    Returns:
        HttpResponse: Página de transferencia o redirección a confirmación.

    """
    pago = get_object_or_404(Pago, id=pago_id, compra__usuario=request.user)

    if request.method == "POST":
        # Simulación: el usuario confirma que realizó la transferencia
        request.FILES.get("comprobante")

        # En un caso real, guardaríamos el comprobante y marcaríamos el pago
        # como pendiente de verificación
        pago.estado = "pagado"  # En producción debería ser 'procesando' hasta verificar
        pago.referencia = f"TRF-{pago.id}"
        pago.save()

        # Actualizar estado de la compra
        compra = pago.compra
        compra.estado = "pagado"
        compra.save()

        # Generar factura
        generar_factura(compra)

        # Enviar correo de confirmación de forma asíncrona
        enviar_correo_confirmacion.delay(compra.id)

        messages.success(
            request,
            "Transferencia registrada con éxito. Procesaremos tu pago "
            "lo antes posible.",
        )
        return redirect("pagos:confirmar_pago", pago_id=pago.id)

    # Datos bancarios para la transferencia
    datos_bancarios = {
        "titular": "ROOT TECHNOLOGIES S.A.",
        "banco": "Banco de Ejemplo",
        "cuenta": "000-123456-789",
        "tipo_cuenta": "Corriente",
        "referencia": f"Compra #{pago.compra.id}",
    }

    return render(request, "pagos/pagoConTransferencia.html", {
        "pago": pago,
        "datos_bancarios": datos_bancarios,
    })


@login_required
def pago_movil(request: HttpRequest, pago_id: int) -> HttpResponse:
    """Gestiona el proceso de pago mediante aplicación móvil (Nequi).

    Args:
        request: La solicitud HTTP.
        pago_id: ID del pago a procesar.

    Returns:
        HttpResponse: Página de pago móvil o redirección a confirmación.

    """
    pago = get_object_or_404(Pago, id=pago_id, compra__usuario=request.user)

    if request.method == "POST":
        # Procesamiento del pago móvil
        numero_telefono = request.POST.get("numero_telefono")

        if not numero_telefono:
            messages.error(request, "El número de teléfono es obligatorio")
            return render(request, "pagos/pagoMovil.html", {"pago": pago})

        # Simulamos procesamiento exitoso
        pago.estado = "pagado"
        pago.referencia = f"NEQ-{pago.id}"
        pago.save()

        # Actualizar estado de la compra
        compra = pago.compra
        compra.estado = "pagado"
        compra.save()

        # Generar factura
        generar_factura(compra)

        # Enviar correo de confirmación
        enviar_correo_confirmacion.delay(compra.id)

        messages.success(request, "Pago con Nequi procesado con éxito")
        return redirect("pagos:confirmar_pago", pago_id=pago.id)

    return render(request, "pagos/pagoMovil.html", {"pago": pago})


@login_required
def confirmar_pago(request: HttpRequest, pago_id: int) -> HttpResponse:
    """Muestra la confirmación del pago realizado.

    Args:
        request: La solicitud HTTP.
        pago_id: ID del pago confirmado.

    Returns:
        HttpResponse: Página de confirmación del pago.

    """
    pago = get_object_or_404(Pago, id=pago_id, compra__usuario=request.user)
    compra = pago.compra

    # Verificar si existe factura
    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        factura = None

    return render(request, "pagos/confirmacionDePago.html", {
        "pago": pago,
        "compra": compra,
        "factura": factura,
    })
