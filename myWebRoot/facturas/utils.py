"""Utilidades para la generacion de facturas y archivos PDF."""

import time
import uuid
from io import BytesIO
from typing import TYPE_CHECKING

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from pagos.models import Compra
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Solucion para importación cíclica
if TYPE_CHECKING:
    from .models import Factura


def generar_numero_factura_unico(compra=None):
    """Genera un numero de factura único usando multiples estrategias."""
    from .models import Factura

    fecha = timezone.now()
    timestamp = int(time.time() * 1000)

    # Estrategias de numeración en orden de preferencia
    estrategias = [
        # Formato: F20250529-1735471234567
        f"F{fecha.year}{fecha.month:02d}{fecha.day:02d}-{timestamp}",

        # Formato: FAC-123-1735471234567 (con ID de compra)
        f"FAC-{compra.id}-{timestamp}" if compra else f"FAC-NEW-{timestamp}",

        # Formato: ROOT-1735471234567-123
        f"ROOT-{timestamp}-{compra.id if compra else 'NEW'}",

        # Formato: F20250529-ABC12345 (con UUID corto)
        f"F{fecha.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",

        # Formato simple: INV1735471234567
        f"INV{timestamp}",
    ]

    # Probar cada estrategia hasta encontrar un numero unico
    for numero in estrategias:
        if not Factura.objects.filter(numero=numero).exists():
            return numero

    # Ultimo recurso: UUID completo (garantiza unicidad al 100%)
    return f"F-{uuid.uuid4()!s}"


def crear_factura_segura(compra):
    """Crea una factura de forma segura con manejo de errores."""
    from .models import Factura

    max_intentos = 5
    for intento in range(max_intentos):
        try:
            numero = generar_numero_factura_unico(compra)
            return Factura.objects.create(compra=compra, numero=numero)

        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e) and "numero" in str(e):
                if intento == max_intentos - 1:
                    # Ultimo intento: usar UUID garantizado
                    numero_emergencia = f"F-RECOVERY-{str(uuid.uuid4())[:12]}"
                    return Factura.objects.create(compra=compra, numero=numero_emergencia)
                continue
            raise
        except Exception:
            if intento == max_intentos - 1:
                raise
    return None


def generar_factura(compra: Compra) -> "Factura":
    """Genera una factura para una compra realizada."""
    # Importar aquí para evitar importaciones circulares
    from .models import Factura

    # Verificar si ya existe una factura para esta compra
    try:
        return compra.factura
    except Factura.DoesNotExist:
        pass

    # Crear la factura usando transacción para seguridad
    try:
        with transaction.atomic():
            # Crear la factura con número único
            factura = crear_factura_segura(compra)

            # Generar el PDF
            generar_pdf_factura(factura)

            return factura

    except IntegrityError:
        # Intentar obtener la factura que pudo haberse creado por otro proceso
        try:
            return compra.factura
        except Factura.DoesNotExist:
            msg = "No se pudo crear la factura después de múltiples intentos"
            raise Exception(msg)
    except Exception:
        raise


def generar_pdf_factura(factura: "Factura") -> None:
    """Genera el archivo PDF para una factura."""
    try:
        compra = factura.compra

        # Crea un espacio de memoria para el pdf
        buffer = BytesIO()

        # Valida que el docmumento se creo
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        style_title = styles["Title"]
        style_heading = styles["Heading1"]
        style_normal = styles["Normal"]

        # Titulo de la factura
        elements.append(Paragraph(f"FACTURA #{factura.numero}", style_title))
        elements.append(Spacer(1, 20))

        # Informacion de la empresa que emite la factua
        elements.append(Paragraph("ROOTAPP S.A.", style_heading))
        elements.append(Paragraph("NIT: 900.123.456-7", style_normal))
        elements.append(Paragraph("Dirección: Calle Principal #123", style_normal))
        elements.append(Paragraph("Teléfono: +57 3105816209", style_normal))
        elements.append(Paragraph("Email: info@rootapp.com", style_normal))
        elements.append(Spacer(1, 20))

        # Informacion del usuario o cliente
        elements.append(Paragraph("Datos del Cliente", style_heading))
        elements.append(Paragraph(f"Nombre: {compra.usuario.get_full_name() or compra.usuario.username}",style_normal))
        elements.append(Paragraph(f"Documento: {getattr(compra.usuario, 'id_documento', 'No registrado') or 'No registrado'}",style_normal))
        elements.append(Paragraph(f"Dirección: {getattr(compra, 'direccion_entrega', 'No especificada') or 'No especificada'}",style_normal))
        elements.append(Paragraph(f"Email: {compra.usuario.email}", style_normal))
        elements.append(Spacer(1, 20))

        # Informacion Relevante de la compra realizada
        elements.append(Paragraph("Detalles de la Compra", style_heading))
        elements.append(Paragraph(f"Compra #: {compra.id}", style_normal))
        elements.append(Paragraph(f"Fecha: {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}", style_normal))
        elements.append(Spacer(1, 10))

        # Tabla del producto que se compro
        data = [["Producto", "Código", "Cantidad", "Precio Unitario", "Subtotal"]]

        # Valida si hay detalle de una compra para poder imprimirlo
        detalles = compra.detalles.all() if hasattr(compra, "detalles") else []

        if detalles:
            # Usar list comprehension para optimizar el bucle
            data.extend([[detalle.producto.nombre,getattr(detalle.producto, "codigo", "N/A"),str(detalle.cantidad),f"${detalle.precio_unitario:.2f}",f"${detalle.subtotal:.2f}"]for detalle in detalles])
        else:
            # Si no encuentra detalles, muestra la informacion basica
            data.append(["Compra general",f"COMP-{compra.id}","1",f"${compra.total:.2f}",f"${compra.total:.2f}"])

        # Agrega el total
        data.append(["", "", "", "TOTAL", f"${compra.total:.2f}"])

        # Crea la tabla
        table = Table(data)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey),("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),("ALIGN", (0, 0), (-1, -1), "CENTER"),("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),("FONTSIZE", (0, 0), (-1, 0), 12),("BOTTOMPADDING", (0, 0), (-1, 0), 12),("BACKGROUND", (0, -1), (-1, -1), colors.beige),("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),("GRID", (0, 0), (-1, -1), 1, colors.black),("ALIGN", (3, 1), (-1, -1), "RIGHT")]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        # Comentarios finales
        elements.append(Paragraph("Gracias por tu compra.", style_normal))
        elements.append(Paragraph("Esta factura es valida como comprobante de pago.",style_normal))
        elements.append(Paragraph("Muestra tu factura al personal encargado en la salida del establecimiento.",style_normal))
        elements.append(Paragraph("Muchas Gracias Por Tu Compra .",style_normal))

        # Generar el DOC PDF
        doc.build(elements)

        # Guarda el PDF en el campo de la factura
        factura.pdf.save(f"factura_{factura.numero}.pdf",ContentFile(buffer.getvalue()),save=False)  # No trigger save() nuevamente)

        # Guarda solo el campo PDF
        from .models import Factura
        Factura.objects.filter(id=factura.id).update(pdf=factura.pdf)

        buffer.close()

    except Exception:
        pass
        # No falla completamente la factura existe pero sin PDF
