"""Vistas para la aplicación de facturas."""

from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from pagos.models import Compra

from .models import Factura
from .utils import generar_factura, generar_pdf_factura


@login_required
def detalle_compra(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Muestra el detalle de una compra con su factura asociada.

    Args:
        request: La solicitud HTTP.
        compra_id: ID de la compra a visualizar.

    Returns:
        HttpResponse: La página de detalle de la compra.

    """
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)

    # Comprobar si tiene factura
    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        factura = None

    return render(request, "facturas/detalle_compra.html", {"compra": compra,"factura": factura})


@login_required
def descargar_factura(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Permite descargar la factura de una compra en formato PDF.

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
        factura = generar_factura(compra)

    # Si por alguna razón no tenemos el PDF, regenerarlo
    pdf_path = Path(factura.pdf.path) if factura.pdf else None
    if not factura.pdf or not pdf_path.exists():
        generar_pdf_factura(factura)

    # Abrir el archivo y retornarlo como respuesta
    pdf_path = Path(factura.pdf.path)
    with pdf_path.open("rb") as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        disposition = f'attachment; filename="factura_{factura.numero}.pdf"'
        response["Content-Disposition"] = disposition
        return response
