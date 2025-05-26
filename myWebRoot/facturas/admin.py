"""Configuración del administrador para la aplicación de facturas."""

from django.contrib import admin

from .models import Factura


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para el modelo Factura."""

    list_display = ("numero", "compra", "fecha_emision")
    search_fields = ("numero", "compra__id", "compra__usuario__username")
    readonly_fields = ("fecha_emision",)
