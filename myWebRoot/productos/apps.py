"""Archivo para la configuracion de la app productos."""
from django.apps import AppConfig


class ProductosConfig(AppConfig):
    """Cofiguracion de la app productos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "productos"
