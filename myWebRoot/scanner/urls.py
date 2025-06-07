"""Modulo de importación de la app de scaneo de productos."""

from django.urls import path

from . import views

app_name = "scanner"
"""Llamada de la App de scaneo para los productos."""
urlpatterns = [path("", views.scanner, name="scanner")]
