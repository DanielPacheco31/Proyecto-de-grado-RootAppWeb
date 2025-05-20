"""Configuración de la aplicación de pagos."""

from django.apps import AppConfig


class PagosConfig(AppConfig):
    """Configuración para la aplicación de pagos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pagos"
