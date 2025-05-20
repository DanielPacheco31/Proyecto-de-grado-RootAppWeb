"""Configuración de la aplicación de facturas."""

from django.apps import AppConfig


class FacturasConfig(AppConfig):
    """Configuración para la aplicación de facturas.

    Esta aplicación gestiona la generación y visualización de facturas
    para las compras realizadas en la tienda.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "facturas"
