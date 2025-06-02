"""Configuración de la aplicación principal."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuracion para la aplicacion principal de ROOT."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
