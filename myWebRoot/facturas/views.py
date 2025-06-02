"""Vistas para la aplicación de facturas."""

from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from pagos.models import Compra
from .models import Factura
from .utils import generar_factura, generar_pdf_factura
from django.db import transaction
from django.http import JsonResponse


@login_required
def detalle_compra(request: HttpRequest, compra_id: int) -> HttpResponse:
    """
    Muestra el detalle de una compra con su factura asociada.

    Args:
        request: La solicitud HTTP.
        compra_id: ID de la compra a visualizar.

    Returns:
        HttpResponse: La página de detalle de la compra.

    """
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    # Verificar si tiene factura
    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        factura = None

    return render(request, "facturas/detalle_compra.html", {
        "compra": compra,
        "factura": factura
    })


@login_required
def descargar_factura(request: HttpRequest, compra_id: int) -> HttpResponse:
    """
    Permite descargar la factura de una compra en formato PDF.

    Args:
        request: La solicitud HTTP.
        compra_id: ID de la compra para la que se descargará la factura.

    Returns:
        HttpResponse: El archivo PDF de la factura.

    """
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        # Si no existe, generarla
        try:
            factura = generar_factura(compra)
            messages.success(request, f'Factura {factura.numero} generada exitosamente')
        except Exception as e:
            messages.error(request, f'Error al generar la factura: {str(e)}')
            return render(request, "facturas/detalle_compra.html", {
                "compra": compra,
                "factura": None
            })

    # Verificar si existe el PDF
    try:
        pdf_path = Path(factura.pdf.path) if factura.pdf else None
        if not factura.pdf or not pdf_path or not pdf_path.exists():
            # Regenerar PDF si no existe
            generar_pdf_factura(factura)
            messages.info(request, 'PDF regenerado exitosamente')

        # Abrir el archivo y retornarlo como respuesta
        pdf_path = Path(factura.pdf.path)
        with pdf_path.open("rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            disposition = f'attachment; filename="factura_{factura.numero}.pdf"'
            response["Content-Disposition"] = disposition
            return response
            
    except Exception as e:
        messages.error(request, f'Error al acceder al PDF: {str(e)}')
        return render(request, "facturas/detalle_compra.html", {
            "compra": compra,
            "factura": factura
        })

@login_required
def cancelar_compra(request, compra_id):
    """
    Cancela una compra si está en estado pendiente.
    
    Args:
        request: HttpRequest
        compra_id: ID de la compra a cancelar
        
    Returns:
        HttpResponse: Redirect o JSON response
    """
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)
    
    if request.method == 'POST':
        # Verificar que la compra se puede cancelar
        if compra.estado != 'pendiente':
            messages.error(request, f'No se puede cancelar una compra en estado "{compra.get_estado_display()}"')
            return redirect('facturas:detalle_compra', compra_id=compra.id)
        
        try:
            with transaction.atomic():
                # Cambiar estado a cancelado
                compra.estado = 'cancelado'
                compra.save()
                
                # Si hay pago asociado, también cancelarlo
                if hasattr(compra, 'pago'):
                    compra.pago.estado = 'cancelado'
                    compra.pago.save()
                
                # Restaurar stock si es necesario
                restaurar_stock_productos(compra)
                
                messages.success(request, f'Compra #{compra.id} cancelada exitosamente')
                
                # Si es petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Compra #{compra.id} cancelada exitosamente'
                    })
                
                return redirect('usuarios:perfil')
                
        except Exception as e:
            messages.error(request, f'Error al cancelar la compra: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al cancelar la compra: {str(e)}'
                })
            
            return redirect('facturas:detalle_compra', compra_id=compra.id)
    
    # GET request - mostrar confirmación
    return render(request, 'facturas/confirmar_cancelacion.html', {
        'compra': compra
    })


def restaurar_stock_productos(compra):
    """
    Restaura el stock de los productos de una compra cancelada.
    
    Args:
        compra: Instancia de Compra
    """
    try:
        for detalle in compra.detalles.all():
            producto = detalle.producto
            if hasattr(producto, 'stock'):
                producto.stock += detalle.cantidad
                producto.save()
                print(f"✅ Stock restaurado para {producto.nombre}: +{detalle.cantidad}")
    except Exception as e:
        print(f"❌ Error restaurando stock: {e}")
        # Log pero no fallar la cancelación por esto