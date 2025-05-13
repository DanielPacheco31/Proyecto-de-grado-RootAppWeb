from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from facturas.models import Factura
from facturas.utils import generar_factura

from .models import Compra, MetodoPago, Pago
from .tasks import enviar_correo_confirmacion


@login_required
def seleccionar_metodo_pago(request, compra_id):
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
def procesar_pago(request, compra_id):
    if request.method != "POST":
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra_id)

    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    # Si la compra ya está pagada, redirigir al detalle
    if compra.estado != "pendiente":
        messages.info(request, "Esta compra ya ha sido procesada")
        return redirect("facturas:detalle_compra", compra_id=compra.id)

    metodo_pago_id = request.POST.get("metodo_pago")
    if not metodo_pago_id:
        messages.error(request, "Debes seleccionar un método de pago")
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)

    # Obtener o crear el método de pago según el ID del formulario
    try:
        # Si es un ID numérico válido de la base de datos
        metodo_id = int(metodo_pago_id)
        try:
            metodo_pago = MetodoPago.objects.get(id=metodo_id, activo=True)
        except MetodoPago.DoesNotExist:
            # Si no existe en la BD, usar el mapeo de IDs de la interfaz
            tipo_metodo = _get_tipo_metodo_por_id_frontend(metodo_pago_id)
            metodo_pago = _obtener_o_crear_metodo_pago(tipo_metodo)
    except (ValueError, TypeError):
        # Si no es un ID numérico, usar el mapeo de IDs de la interfaz
        tipo_metodo = _get_tipo_metodo_por_id_frontend(metodo_pago_id)
        metodo_pago = _obtener_o_crear_metodo_pago(tipo_metodo)

    # Crear el registro de pago
    pago = Pago.objects.create(
        compra=compra,
        metodo_pago=metodo_pago,
        monto=compra.total,
        estado="pendiente",
    )

    # Redirigir según el método de pago
    if metodo_pago.tipo == "nequi":
        return redirect("pagos:pago_movil", pago_id=pago.id)
    elif metodo_pago.tipo in ["bancolombia", "transferencia"]:
        return redirect("pagos:pago_transferencia", pago_id=pago.id)
    elif metodo_pago.tipo in ["pse", "tarjeta"]:
        messages.error(request, "Este método de pago aún no está implementado")
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)
    else:
        messages.error(request, f"Método de pago no válido: {metodo_pago.tipo}")
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)

def _get_tipo_metodo_por_id_frontend(id_frontend):
    """
    Mapea los IDs del frontend a tipos de método de pago
    """
    mapa_ids = {
        "1": "nequi",
        "2": "bancolombia",
        "3": "pse",
        "4": "tarjeta",
    }
    return mapa_ids.get(id_frontend, "transferencia")  # Por defecto transferencia

def _obtener_o_crear_metodo_pago(tipo_metodo):
    """
    Obtiene o crea un método de pago por tipo
    """
    nombres = {
        "nequi": "Nequi",
        "bancolombia": "Bancolombia",
        "pse": "PSE",
        "tarjeta": "Tarjeta de Crédito",
        "transferencia": "Transferencia Bancaria",
        "movil": "Pago Móvil"
    }
    
    metodo_pago, created = MetodoPago.objects.get_or_create(
        tipo=tipo_metodo,
        defaults={
            'nombre': nombres.get(tipo_metodo, tipo_metodo.capitalize()),
            'activo': True
        }
    )
    return metodo_pago

@login_required
def pago_transferencia(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, compra__usuario=request.user)

    if request.method == "POST":
        # Simulación: el usuario confirma que realizó la transferencia
        comprobante = request.FILES.get("comprobante")

        # En un caso real, guardaríamos el comprobante y marcaríamos el pago como pendiente de verificación
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

        messages.success(request, "Transferencia registrada con éxito. Procesaremos tu pago lo antes posible.")
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
def pago_movil(request, pago_id):
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
def confirmar_pago(request, pago_id):
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