from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from facturas.models import Factura
from facturas.utils import generar_factura  # type: ignore

from .models import Compra, MetodoPago, Pago
from .tasks import enviar_correo_confirmacion  # type: ignore


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

# En pagos/views.py
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

    metodo_pago = get_object_or_404(MetodoPago, id=metodo_pago_id, activo=True)

    # Crear el registro de pago
    pago = Pago.objects.create(
        compra=compra,
        metodo_pago=metodo_pago,
        monto=compra.total,
        estado="pendiente",
    )

    # Redirigir según el método de pago
    # Eliminar la redirección a pago con tarjeta
    if metodo_pago.tipo == "transferencia":
        return redirect("pagos:pago_transferencia", pago_id=pago.id)
    if metodo_pago.tipo == "movil":
        return redirect("pagos:pago_movil", pago_id=pago.id)
    messages.error(request, "Método de pago no implementado")
    return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)

@login_required
def pago_transferencia(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, compra__usuario=request.user)

    if request.method == "POST":
        # Simulación: el usuario confirma que realizó la transferencia
        comprobante = request.FILES.get("comprobante")

        # En un caso real, guardaríamos el comprobante y marcaríamos el pago como pendiente de verificación
        pago.estado = "completado"  # En producción debería ser 'procesando' hasta verificar
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

# En views.py
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
        pago.estado = "completado"
        pago.referencia = f"MOV-{pago.id}"
        pago.save()

        # Actualizar estado de la compra
        compra = pago.compra
        compra.estado = "pagado"
        compra.save()

        # Generar factura
        generar_factura(compra)

        # Enviar correo de confirmación
        enviar_correo_confirmacion.delay(compra.id)

        messages.success(request, "Pago móvil procesado con éxito")
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
