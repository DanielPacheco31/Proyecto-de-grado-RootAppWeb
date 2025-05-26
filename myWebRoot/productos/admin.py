"""Configuracion de admin para la app productos."""
from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Configuración del admin para Categorías."""

    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración del admin para Productos."""

    list_display = ("nombre", "codigo", "precio", "stock", "categoria", "texto_estado_stock")
    list_filter = ("categoria", "fecha_creacion", "stock")  # Cambiamos estado_stock por stock
    search_fields = ("nombre", "codigo", "descripcion")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")

    # Campos que se mostrarán al crear/editar un producto
    fieldsets = (
        ("Información Básica", {
            "fields": ("nombre", "codigo", "descripcion", "categoria"),
        }),
        ("Detalles de Precio y Stock", {
            "fields": ("precio", "stock", "imagen"),
        }),
        ("Información de Sistema", {
            "fields": ("fecha_creacion", "fecha_actualizacion"),
            "classes": ("collapse",),
        }),
    )
