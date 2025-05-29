"""Utilidades para la generación de facturas y archivos PDF."""

from io import BytesIO
from typing import TYPE_CHECKING
import time
import uuid

from django.core.files.base import ContentFile
from django.db import transaction, IntegrityError
from django.utils import timezone
from pagos.models import Compra
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Solución para importación cíclica
if TYPE_CHECKING:
    from .models import Factura


def generar_numero_factura_unico(compra=None):
    """
    Genera un número de factura único usando múltiples estrategias.
    
    Args:
        compra: Instancia de compra (opcional)
        
    Returns:
        str: Número de factura único
    """
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
    
    # Probar cada estrategia hasta encontrar un número único
    for numero in estrategias:
        if not Factura.objects.filter(numero=numero).exists():
            return numero
    
    # Último recurso: UUID completo (garantiza unicidad al 100%)
    return f"F-{str(uuid.uuid4())}"


def crear_factura_segura(compra):
    """
    Crea una factura de forma segura con manejo de errores.
    
    Args:
        compra: Instancia de Compra
        
    Returns:
        Factura: La factura creada
    """
    from .models import Factura
    
    max_intentos = 5
    for intento in range(max_intentos):
        try:
            numero = generar_numero_factura_unico(compra)
            factura = Factura.objects.create(compra=compra, numero=numero)
            print(f"✅ Factura creada exitosamente: {factura.numero}")
            return factura
            
        except IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e) and 'numero' in str(e):
                if intento == max_intentos - 1:
                    # Último intento: usar UUID garantizado
                    numero_emergencia = f"F-RECOVERY-{str(uuid.uuid4())[:12]}"
                    factura = Factura.objects.create(compra=compra, numero=numero_emergencia)
                    print(f"✅ Factura de emergencia creada: {factura.numero}")
                    return factura
                continue
            else:
                raise
        except Exception as e:
            print(f"❌ Error en intento {intento + 1}: {e}")
            if intento == max_intentos - 1:
                raise


def generar_factura(compra: Compra) -> "Factura":
    """
    Genera una factura para una compra realizada.

    Args:
        compra: La compra para la que se generará la factura.

    Returns:
        Factura: La factura generada o existente para la compra.

    """
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
            
    except IntegrityError as e:
        print(f"❌ Error de integridad al crear factura: {e}")
        # Intentar obtener la factura que pudo haberse creado por otro proceso
        try:
            return compra.factura
        except Factura.DoesNotExist:
            raise Exception("No se pudo crear la factura después de múltiples intentos")
    except Exception as e:
        print(f"❌ Error general al crear factura: {e}")
        raise


def generar_pdf_factura(factura: "Factura") -> None:
    """
    Genera el archivo PDF para una factura.

    Args:
        factura: La factura para la que se generará el PDF.

    Returns:
        None

    """
    try:
        compra = factura.compra

        # Crear un buffer para el PDF
        buffer = BytesIO()

        # Configurar el documento
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        style_title = styles["Title"]
        style_heading = styles["Heading1"]
        style_normal = styles["Normal"]

        # Título
        elements.append(Paragraph(f"FACTURA #{factura.numero}", style_title))
        elements.append(Spacer(1, 20))

        # Información de la empresa
        elements.append(Paragraph("ROOTAPP S.A.", style_heading))
        elements.append(Paragraph("NIT: 900.123.456-7", style_normal))
        elements.append(Paragraph("Dirección: Calle Principal #123", style_normal))
        elements.append(Paragraph("Teléfono: +57 3105816209", style_normal))
        elements.append(Paragraph("Email: info@rootapp.com", style_normal))
        elements.append(Spacer(1, 20))

        # Información del cliente
        elements.append(Paragraph("DATOS DEL CLIENTE", style_heading))
        elements.append(
            Paragraph(
                f"Nombre: {compra.usuario.get_full_name() or compra.usuario.username}",
                style_normal,
            ),
        )
        elements.append(
            Paragraph(
                f"Documento: {getattr(compra.usuario, 'id_documento', 'No registrado') or 'No registrado'}",
                style_normal,
            ),
        )
        elements.append(
            Paragraph(
                f"Dirección: {getattr(compra, 'direccion_entrega', 'No especificada') or 'No especificada'}",
                style_normal,
            ),
        )
        elements.append(Paragraph(f"Email: {compra.usuario.email}", style_normal))
        elements.append(Spacer(1, 20))

        # Información de la compra
        elements.append(Paragraph("DETALLES DE LA COMPRA", style_heading))
        elements.append(Paragraph(f"Compra #: {compra.id}", style_normal))
        elements.append(Paragraph(f"Fecha: {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}", style_normal,),)
        elements.append(Spacer(1, 10))

        # Tabla de productos
        data = [["Producto", "Código", "Cantidad", "Precio Unitario", "Subtotal"]]

        # Verificar si hay detalles de compra
        detalles = compra.detalles.all() if hasattr(compra, 'detalles') else []
        
        if detalles:
            # Usar list comprehension para optimizar el bucle
            data.extend([
                [
                    detalle.producto.nombre,
                    getattr(detalle.producto, 'codigo', 'N/A'),
                    str(detalle.cantidad),
                    f"${detalle.precio_unitario:.2f}",
                    f"${detalle.subtotal:.2f}",
                ]
                for detalle in detalles
            ])
        else:
            # Si no hay detalles, mostrar información básica
            data.append(["Compra general",f"COMP-{compra.id}","1",f"${compra.total:.2f}",f"${compra.total:.2f}",])

        # Agregar el total
        data.append(["", "", "", "TOTAL", f"${compra.total:.2f}"])

        # Crear la tabla
        table = Table(data)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey),("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),("ALIGN", (0, 0), (-1, -1), "CENTER"),("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),("FONTSIZE", (0, 0), (-1, 0), 12),("BOTTOMPADDING", (0, 0), (-1, 0), 12),("BACKGROUND", (0, -1), (-1, -1), colors.beige),("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),("GRID", (0, 0), (-1, -1), 1, colors.black),("ALIGN", (3, 1), (-1, -1), "RIGHT"),]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        # Comentarios finales
        elements.append(Paragraph("Gracias por tu compra.", style_normal))
        elements.append(Paragraph("Esta factura es válida como comprobante de pago.",style_normal,),)

        # Generar el PDF
        doc.build(elements)

        # Guardar el PDF en el campo de la factura
        factura.pdf.save(f"factura_{factura.numero}.pdf",ContentFile(buffer.getvalue()),save=False)  # No trigger save() nuevamente)
        
        # Guardar solo el campo PDF
        from .models import Factura
        Factura.objects.filter(id=factura.id).update(pdf=factura.pdf)

        buffer.close()
        print(f"✅ PDF generado exitosamente para factura {factura.numero}")
        
    except Exception as e:
        print(f"❌ Error generando PDF para factura {factura.numero}: {e}")
        # No fallar completamente, la factura existe aunque sin PDF