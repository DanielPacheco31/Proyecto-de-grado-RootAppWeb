"""Configuración del administrador para la aplicación de facturas."""

from django.contrib import admin
from django.http import HttpRequest

from .models import Factura


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para el modelo Factura."""

    list_display = ("numero", "compra", "fecha_emision")
    search_fields = ("numero", "compra__id", "compra__usuario__username")
    readonly_fields = ("fecha_emision",)

    def has_add_permission(self, _: HttpRequest) -> bool:
        """Verifica si el usuario tiene permiso para agregar facturas.

        Args:
            _: La solicitud HTTP (no utilizada).

        Returns:
            bool: False, ya que las facturas se crean automáticamente.

        """
        # Las facturas se crean automáticamente, no manualmente
        return False
