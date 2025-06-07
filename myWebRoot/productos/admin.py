"""Configuracion de admin para la app productos."""
from typing import ClassVar

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Configuración del admin para Categorías."""

    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración del admin para Productos."""

    list_display = ("nombre", "codigo", "precio", "stock", "categoria", "qr_mini", "acciones_qr")
    list_filter = ("categoria", "fecha_creacion", "stock")
    search_fields = ("nombre", "codigo", "descripcion")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "qr_code_display", "qr_urls")

    # Campos que se mostrarán al crear/editar un producto
    fieldsets = (
        ("Información Básica", {"fields": ("nombre", "codigo", "descripcion", "categoria")}),
        ("Detalles de Precio y Stock", {"fields": ("precio", "stock", "imagen")}),
        ("Códigos QR y Barras", {"fields": ("qr_code_display", "qr_urls"),"classes": ("collapse",),"description": "Códigos QR y de barras generados automáticamente para este producto"}),
        ("Información de Sistema", {"fields": ("fecha_creacion", "fecha_actualizacion"),"classes": ("collapse",)}),
        )

    def qr_mini(self, obj: Producto) -> SafeString | str:
        """Muestra un QR pequeño en la lista."""
        if obj.codigo:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=50x50&data={obj.codigo}"
            return format_html(
                '<img src="{}" width="25" height="25" title="QR: {}" style="border: 1px solid #ddd; border-radius: 3px;"/>',
                qr_url, obj.codigo,
            )
        return "Sin código"
    qr_mini.short_description = "QR"

    def acciones_qr(self, obj: Producto) -> SafeString | str:
        """Botones de acción para QR."""
        if obj.codigo:
            return format_html(
                """
                <a href="#" onclick="mostrarQRModal('{}', '{}'); return false;"
                   class="button" style="background: #0066FF; color: white; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">
                   📱 Ver QR
                </a>
                <a href="https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={}"
                   target="_blank" class="button" style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-left: 3px;">
                   📥 Descargar
                </a>
                """,
                obj.codigo, obj.nombre, obj.codigo,
            )
        return "Sin código"
    acciones_qr.short_description = "Acciones"

    def qr_code_display(self, obj: Producto) -> SafeString:
        """Campo readonly que muestra el QR grande."""
        if obj.codigo:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={obj.codigo}"
            barcode_url = f"https://barcodeapi.org/api/128/{obj.codigo}"

            return format_html(
                """
                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 2px solid #0066FF;">
                    <h3 style="color: #0066FF; margin-bottom: 20px;">📱 Códigos para: {}</h3>

                    <!-- Código QR -->
                    <div style="margin-bottom: 30px;">
                        <h4 style="color: #333; margin-bottom: 10px;">Código QR</h4>
                        <img src="{}" style="border: 3px solid #0066FF; border-radius: 8px; background: white; padding: 10px;"/>
                        <br><br>
                        <a href="{}" target="_blank"
                           style="background: #28a745; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; margin: 5px;">
                            📥 Descargar QR (400x400)
                        </a>
                        <a href="https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={}" target="_blank"
                           style="background: #17a2b8; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; margin: 5px;">
                            📄 QR Alta Resolución
                        </a>
                    </div>

                    <!-- Código de Barras -->
                    <div style="margin-bottom: 20px;">
                        <h4 style="color: #333; margin-bottom: 10px;">Código de Barras</h4>
                        <img src="{}" style="border: 2px solid #666; border-radius: 4px; background: white; padding: 5px;" onerror="this.style.display='none'"/>
                        <br><br>
                        <a href="{}" target="_blank"
                           style="background: #6f42c1; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; margin: 5px;">
                            📊 Ver Código de Barras
                        </a>
                    </div>

                    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <p style="margin: 0; color: #1976d2;"><strong>Código:</strong> <span style="font-family: monospace; font-size: 18px; background: white; padding: 5px 10px; border-radius: 4px;">{}</span></p>
                        <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">
                            💡 <strong>Tip:</strong> Usa estos códigos en tu app scanner para probar la funcionalidad
                        </p>
                    </div>
                </div>
                """,
                obj.nombre, qr_url, qr_url, obj.codigo, barcode_url, barcode_url, obj.codigo,
            )
        return format_html(
            '<div style="text-align: center; padding: 20px; background: #fff3cd; border-radius: 8px; color: #856404;">'
            '<p>⚠️ Debe guardar el producto primero para generar los códigos</p>'
            '</div>',
        )
    qr_code_display.short_description = "Códigos QR y Barras"

    def qr_urls(self, obj: Producto) -> SafeString | str:
        """URLs útiles para los códigos."""
        if obj.codigo:
            return format_html(
                """
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px;">
                    <p><strong>QR Pequeño (200x200):</strong><br>
                    <a href="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={}" target="_blank">
                    https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={}</a></p>

                    <p><strong>QR Grande (600x600):</strong><br>
                    <a href="https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={}" target="_blank">
                    https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={}</a></p>

                    <p><strong>Código de Barras:</strong><br>
                    <a href="https://barcodeapi.org/api/128/{}" target="_blank">
                    https://barcodeapi.org/api/128/{}</a></p>

                    <div style="background: #e3f2fd; padding: 10px; border-radius: 4px; margin-top: 10px;">
                        <p style="margin: 0; color: #1976d2;"><strong>📋 Para usar en tu app:</strong></p>
                        <p style="margin: 5px 0 0 0; color: #666;">
                        1. Copia cualquiera de estos enlaces<br>
                        2. Ábrelo en otra pantalla/dispositivo<br>
                        3. Escanéalo con tu app ROOT scanner
                        </p>
                    </div>
                </div>
                """,
                obj.codigo, obj.codigo, obj.codigo, obj.codigo, obj.codigo, obj.codigo,
            )
        return "Sin código disponible"
    qr_urls.short_description = "URLs de códigos (para desarrolladores)"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Producto]:
        """Optimizar consultas incluyendo categoria."""
        return super().get_queryset(request).select_related("categoria")

    class Media:
        """Archivos CSS y JS para el admin."""

        js: ClassVar[tuple[str, ...]] = ("admin/js/productos_qr.js",)
        css: ClassVar[dict[str, tuple[str, ...]]] = {"all": ("admin/css/productos_qr.css",)}
