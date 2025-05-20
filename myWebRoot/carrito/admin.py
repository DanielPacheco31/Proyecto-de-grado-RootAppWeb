"""Configuración del administrador para la aplicación carrito."""

from django.contrib import admin

from .models import Carrito, CarritoItem

# Registra tus modelos aquí
admin.site.register(Carrito)
admin.site.register(CarritoItem)
