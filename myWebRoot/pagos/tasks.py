from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def enviar_correo_confirmacion(compra_id):
    """Envía un correo de confirmación de compra"""
    try:
        # Importar aquí para evitar importaciones circulares
        from .models import Compra
        
        compra = Compra.objects.select_related('usuario').prefetch_related('detalles__producto').get(id=compra_id)
        
        # Construir el mensaje
        asunto = f'Confirmación de compra #{compra.id}'
        mensaje = f"""
        Hola {compra.usuario.first_name or compra.usuario.username},
        
        ¡Gracias por tu compra! Tu pedido #{compra.id} ha sido recibido y está siendo procesado.
        
        Resumen de tu pedido:
        """
        
        for detalle in compra.detalles.all():
            mensaje += f"\n- {detalle.cantidad}x {detalle.producto.nombre}: ${detalle.subtotal}"
        
        mensaje += f"\n\nTotal: ${compra.total}"
        
        # Enviar el correo
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [compra.usuario.email],
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False