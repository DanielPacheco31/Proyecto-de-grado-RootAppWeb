from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import os
from .models import Factura
from pagos.models import Compra
from .utils import generar_factura, generar_pdf_factura # type: ignore

@login_required
def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)
    
    # Comprobar si tiene factura
    try:
        factura = compra.factura
    except:
        factura = None
        
    return render(request, 'facturas/detalle_compra.html', {
        'compra': compra,
        'factura': factura
    })

@login_required
def descargar_factura(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id, usuario=request.user)
    
    try:
        factura = compra.factura
    except Factura.DoesNotExist:
        # Si no existe, generarla
        factura = generar_factura(compra)
    
    # Si por alguna razón no tenemos el PDF, regenerarlo
    if not factura.pdf or not os.path.exists(factura.pdf.path):
        generar_pdf_factura(factura)
    
    # Abrir el archivo y retornarlo como respuesta
    with open(factura.pdf.path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero}.pdf"'
        return response