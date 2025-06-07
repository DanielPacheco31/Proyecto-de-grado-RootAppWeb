"""Utilidades para la generacion de facturas y archivos PDF."""

import logging
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

# Logger para el módulo
logger = logging.getLogger(__name__)


class FacturaCreationError(Exception):
    """Excepción personalizada para errores en la creación de facturas."""


def generar_numero_factura_unico(compra: Compra | None = None) -> str:
    """Genera un numero de factura único usando multiples estrategias."""
    from .models import Factura

    fecha = timezone.now()
    timestamp = int(time.time() * 1000)

    # Estrategias de numeración en orden de preferencia
    estrategias = [
        f"F{fecha.year}{fecha.month:02d}{fecha.day:02d}-{timestamp}",
        f"FAC-{compra.id}-{timestamp}" if compra else f"FAC-NEW-{timestamp}",
        f"ROOT-{timestamp}-{compra.id if compra else 'NEW'}",
        f"F{fecha.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
        f"INV{timestamp}",
    ]

    # Probar cada estrategia hasta encontrar un numero unico
    for numero in estrategias:
        if not Factura.objects.filter(numero=numero).exists():
            return numero

    # Ultimo recurso: UUID completo (garantiza unicidad al 100%)
    return f"F-{uuid.uuid4()!s}"


def crear_factura_segura(compra: Compra) -> "Factura":
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
            raise FacturaCreationError(msg) from None
    except Exception:
        raise


def _crear_encabezado_factura(factura: "Factura", elements: list, styles: dict) -> None:
    """Crea el encabezado de la factura."""
    elements.append(Paragraph(f"FACTURA #{factura.numero}", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Información de la empresa
    elements.append(Paragraph("ROOTAPP S.A.", styles["Heading1"]))
    elements.append(Paragraph("NIT: 900.123.456-7", styles["Normal"]))
    elements.append(Paragraph("Dirección: Calle Principal #123", styles["Normal"]))
    elements.append(Paragraph("Teléfono: +57 3105816209", styles["Normal"]))
    elements.append(Paragraph("Email: info@rootapp.com", styles["Normal"]))
    elements.append(Spacer(1, 20))


def _crear_datos_cliente(compra: Compra, elements: list, styles: dict) -> None:
    """Crea la sección de datos del cliente."""
    elements.append(Paragraph("Datos del Cliente", styles["Heading1"]))
    elements.append(Paragraph(f"Nombre: {compra.usuario.get_full_name() or compra.usuario.username}", styles["Normal"]))
    elements.append(Paragraph(f"Documento: {getattr(compra.usuario, 'id_documento', 'No registrado') or 'No registrado'}", styles["Normal"]))
    elements.append(Paragraph(f"Dirección: {getattr(compra, 'direccion_entrega', 'No especificada') or 'No especificada'}", styles["Normal"]))
    elements.append(Paragraph(f"Email: {compra.usuario.email}", styles["Normal"]))
    elements.append(Spacer(1, 20))


def _crear_detalles_compra(compra: Compra, elements: list, styles: dict) -> None:
    """Crea la sección de detalles de compra."""
    elements.append(Paragraph("Detalles de la Compra", styles["Heading1"]))
    elements.append(Paragraph(f"Compra #: {compra.id}", styles["Normal"]))
    elements.append(Paragraph(f"Fecha: {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 10))


def _crear_tabla_productos(compra: Compra, elements: list) -> None:
    """Crea la tabla de productos de la compra."""
    data = [["Producto", "Código", "Cantidad", "Precio Unitario", "Subtotal"]]

    detalles = compra.detalles.all() if hasattr(compra, "detalles") else []

    if detalles:
        data.extend([
            [
                detalle.producto.nombre,
                getattr(detalle.producto, "codigo", "N/A"),
                str(detalle.cantidad),
                f"${detalle.precio_unitario:.2f}",
                f"${detalle.subtotal:.2f}",
            ]
            for detalle in detalles
        ])
    else:
        data.append([
            "Compra general",
            f"COMP-{compra.id}",
            "1",
            f"${compra.total:.2f}",
            f"${compra.total:.2f}",
        ])

    data.append(["", "", "", "TOTAL", f"${compra.total:.2f}"])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, -1), (-1, -1), colors.beige),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))


def _crear_comentarios_finales(elements: list, styles: dict) -> None:
    """Crea los comentarios finales de la factura."""
    elementos_finales = [
        "Gracias por tu compra.",
        "Esta factura es valida como comprobante de pago.",
        "Muestra tu factura al personal encargado en la salida del establecimiento.",
        "Muchas Gracias Por Tu Compra .",
    ]

    elements.extend(Paragraph(comentario, styles["Normal"]) for comentario in elementos_finales)


def generar_pdf_factura(factura: "Factura") -> None:
    """Genera el archivo PDF para una factura."""
    try:
        compra = factura.compra
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Crear secciones de la factura
        _crear_encabezado_factura(factura, elements, styles)
        _crear_datos_cliente(compra, elements, styles)
        _crear_detalles_compra(compra, elements, styles)
        _crear_tabla_productos(compra, elements)
        _crear_comentarios_finales(elements, styles)

        # Generar el documento PDF
        doc.build(elements)

        # Guardar el PDF
        factura.pdf.save(
            f"factura_{factura.numero}.pdf",
            ContentFile(buffer.getvalue()),
            save=False,
        )

        # Actualizar solo el campo PDF
        from .models import Factura
        Factura.objects.filter(id=factura.id).update(pdf=factura.pdf)
        buffer.close()

    except Exception:
        logger.exception("Error generando PDF de factura %s", factura.numero)
        raise
