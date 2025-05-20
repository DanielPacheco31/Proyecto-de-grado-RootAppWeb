"""Configuración de la aplicación carrito."""

from django.apps import AppConfig


class CarritoConfig(AppConfig):
    """Configuración para la aplicación de carrito de compras."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "carrito"
