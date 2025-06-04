"""Tareas asíncronas para la aplicación de pagos."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def enviar_correo_confirmacion(compra_id: int) -> bool | None:
    """
    Envía un correo de confirmación de compra.

    Args:
        compra_id: ID de la compra para la que se enviará la confirmación.

    Returns:
        bool | None: True si el correo se envió correctamente, False en caso de error.

    """
    try:
        # Importar aquí para evitar importaciones circulares
        from .models import Compra

        compra = Compra.objects.select_related("usuario").prefetch_related(
            "detalles__producto",
        ).get(id=compra_id)

        # Construir el mensaje
        asunto = f"Confirmación de compra #{compra.id}"
        mensaje = f"""
        Hola {compra.usuario.first_name or compra.usuario.username},

        ¡Gracias por tu compra! Tu pedido #{compra.id} ha sido recibido y está siendo
        procesado.

        Resumen de tu pedido:
        """

        for detalle in compra.detalles.all():
            mensaje += (
                f"\n- {detalle.cantidad}x {detalle.producto.nombre}: "
                f"${detalle.subtotal}"
            )

        mensaje += f"\n\nTotal: ${compra.total}"

        # Enviar el correo
        send_mail(asunto,mensaje,settings.DEFAULT_FROM_EMAIL,[compra.usuario.email],fail_silently=False,)
    except (Compra.DoesNotExist, ValueError, ConnectionError):
        # Especificamos excepciones concretas en lugar de Exception genérica
        return False
    else:
        return True
