"""Aplicación de facturas para gestionar la emisión de facturas de la tienda."""
from django.apps import AppConfig


class ScannerConfig(AppConfig):
    """Modelo de Scanner de productos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "scanner"
