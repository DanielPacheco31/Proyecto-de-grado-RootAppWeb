"""Configuración de la aplicación principal."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuración para la aplicación principal de ROOT.

    Esta aplicación gestiona las vistas principales como la página de inicio,
    información institucional y contacto.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
