from django.contrib import admin

from .models import Factura


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("numero", "compra", "fecha_emision")
    search_fields = ("numero", "compra__id", "compra__usuario__username")
    readonly_fields = ("fecha_emision",)

    def has_add_permission(self, request):
        # Las facturas se crean automáticamente, no manualmente
        return False
