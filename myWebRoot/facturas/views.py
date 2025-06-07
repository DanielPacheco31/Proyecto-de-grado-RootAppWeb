"""Vistas para la aplicación de facturas."""

import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from pagos.models import Compra

from .models import Factura
from .utils import FacturaCreationError, generar_factura, generar_pdf_factura

# Logger para el módulo
logger = logging.getLogger(__name__)


@login_required
def detalle_compra(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Detalle de compra + factura de la compra."""
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        factura = None

    return render(request, "facturas/detalle_compra.html", {"compra": compra,"factura": factura})


@login_required
def descargar_factura(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Decarga la fac de compra en pdf."""
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    try:
        factura = compra.factura
    except Factura.DoesNotExist:

        try:
            factura = generar_factura(compra)
            messages.success(request, f"Factura {factura.numero} generada exitosamente")
        except (FacturaCreationError, IntegrityError, ValueError) as e:
            messages.error(request, f"error al realizar la factura: {e!s}")
            return render(request, "facturas/detalle_compra.html", {"compra": compra,"factura": None})

    try:
        pdf_path = Path(factura.pdf.path) if factura.pdf else None
        if not factura.pdf or not pdf_path or not pdf_path.exists():
            generar_pdf_factura(factura)
            messages.info(request, "PDF regenerado exitosamente")

        pdf_path = Path(factura.pdf.path)
        with pdf_path.open("rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            disposition = f'attachment; filename="factura_{factura.numero}.pdf"'
            response["Content-Disposition"] = disposition
            return response

    except (OSError, ValueError) as e:
        messages.error(request, f"Error al ubicar al PDF: {e!s}")
        return render(request, "facturas/detalle_compra.html", {"compra": compra,"factura": factura})

@login_required
def cancelar_compra(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Para cancelar una compra en estado pendiente."""
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    if request.method == "POST":
        if compra.estado != "pendiente":
            messages.error(request, f'No se puede cancelar una compra en estado "{compra.get_estado_display()}"')
            return redirect("facturas:detalle_compra", compra_id=compra.id)

        try:
            with transaction.atomic():
                compra.estado = "cancelado"
                compra.save()

                if hasattr(compra, "pago"):
                    compra.pago.estado = "cancelado"
                    compra.pago.save()

                restaurar_stock_productos(compra)

                messages.success(request, f"Compra #{compra.id} cancelada exitosamente")

                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True, "message": f"Compra #{compra.id} cancelada exitosamente"})

                return redirect("usuarios:perfil")

        except (IntegrityError, ValueError, AttributeError) as e:
            messages.error(request, f"Error al cancelar la compra: {e!s}")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False,"message": f"Error al cancelar la compra: {e!s}"})

            return redirect("facturas:detalle_compra", compra_id=compra.id)

    return render(request, "facturas/confirmar_cancelacion.html", {"compra": compra})


def restaurar_stock_productos(compra: Compra) -> None:
    """Devuelve el producto cancelado al stock."""
    try:
        for detalle in compra.detalles.all():
            producto = detalle.producto
            if hasattr(producto, "stock"):
                producto.stock += detalle.cantidad
                producto.save()
    except (AttributeError, ValueError, TypeError) as e:
        logger.warning("Error restaurando stock para compra %s: %s", compra.id, e)
