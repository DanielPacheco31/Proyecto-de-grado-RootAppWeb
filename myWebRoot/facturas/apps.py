"""Configuración de la aplicación de facturas."""

from django.apps import AppConfig


class FacturasConfig(AppConfig):
    """Configuración para la aplicación de facturas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "facturas"
