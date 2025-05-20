"""Configuración del administrador para la aplicación de pagos."""

from django.contrib import admin

from .models import Compra, DetalleCompra, MetodoPago, Pago

# Registra tus modelos aquí
admin.site.register(Compra)
admin.site.register(DetalleCompra)
admin.site.register(MetodoPago)
admin.site.register(Pago)
# Register your models here.
