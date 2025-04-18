from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

def generar_factura(compra):
    """Genera una factura para una compra realizada"""
    # Importar aquí para evitar importaciones circulares
    from .models import Factura
    
    # Verificar si ya existe
    try:
        factura = compra.factura
        return factura
    except Factura.DoesNotExist:
        # Crear la factura
        factura = Factura.objects.create(compra=compra)
        
        # Generar el PDF
        generar_pdf_factura(factura)
        
        return factura

def generar_pdf_factura(factura):
    """Genera el archivo PDF para una factura"""
    compra = factura.compra
    
    # Crear un buffer para el PDF
    buffer = BytesIO()
    
    # Configurar el documento
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_heading = styles['Heading1']
    style_normal = styles['Normal']
    
    # Título
    elements.append(Paragraph(f"FACTURA #{factura.numero}", style_title))
    elements.append(Spacer(1, 20))
    
    # Información de la empresa
    elements.append(Paragraph("ROOT TECHNOLOGIES S.A.", style_heading))
    elements.append(Paragraph("NIT: 900.123.456-7", style_normal))
    elements.append(Paragraph("Dirección: Calle Principal #123", style_normal))
    elements.append(Paragraph("Teléfono: +57 3105816209", style_normal))
    elements.append(Paragraph("Email: info@rootapp.com", style_normal))
    elements.append(Spacer(1, 20))
    
    # Información del cliente
    elements.append(Paragraph("DATOS DEL CLIENTE", style_heading))
    elements.append(Paragraph(f"Nombre: {compra.usuario.get_full_name() or compra.usuario.username}", style_normal))
    elements.append(Paragraph(f"Documento: {compra.usuario.perfil.id_documento or 'No registrado'}", style_normal))
    elements.append(Paragraph(f"Dirección: {compra.direccion_entrega or 'No especificada'}", style_normal))
    elements.append(Paragraph(f"Email: {compra.usuario.email}", style_normal))
    elements.append(Spacer(1, 20))
    
    # Información de la compra
    elements.append(Paragraph("DETALLES DE LA COMPRA", style_heading))
    elements.append(Paragraph(f"Compra #: {compra.id}", style_normal))
    elements.append(Paragraph(f"Fecha: {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}", style_normal))
    elements.append(Spacer(1, 10))
    
    # Tabla de productos
    data = [["Producto", "Código", "Cantidad", "Precio Unitario", "Subtotal"]]
    
    for detalle in compra.detalles.all():
        data.append([
            detalle.producto.nombre,
            detalle.producto.codigo,
            str(detalle.cantidad),
            f"${detalle.precio_unitario:.2f}",
            f"${detalle.subtotal:.2f}"
        ])
    
    # Agregar el total
    data.append(["", "", "", "TOTAL", f"${compra.total:.2f}"])
    
    # Crear la tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Comentarios finales
    elements.append(Paragraph("Gracias por tu compra.", style_normal))
    elements.append(Paragraph("Esta factura es válida como comprobante de pago.", style_normal))
    
    # Generar el PDF
    doc.build(elements)
    
    # Guardar el PDF en el campo de la factura
    factura.pdf.save(
        f'factura_{factura.numero}.pdf',
        ContentFile(buffer.getvalue())
    )
    
    buffer.close()