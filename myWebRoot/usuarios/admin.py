"""Django admin configuración."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin personalizado para el modelo Usuario."""

    # Campos a mostrar en la lista
    list_display = ("username","email","first_name","last_name","telefono","is_active","is_staff","date_joined")

    # Campos por los que se puede filtrar
    list_filter = ("is_staff","is_superuser","is_active","preferencias_notificacion","date_joined")

    # Campos de búsqueda
    search_fields = ("username","email","first_name","last_name","id_documento","telefono")

    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        ("Información básica", {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name","last_name","email","telefono","direccion","id_documento","fecha_nacimiento")}),
        ("Foto de perfil", {"fields": ("foto",)}),
        ("Preferencias", {"fields": ("preferencias_notificacion",)}),
        ("Permisos", {"fields": ("is_active","is_staff","is_superuser","groups","user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login","date_joined")}),
    )

    # Fieldsets para creación de usuario
    add_fieldsets = (
        ("Información requerida", {"classes": ("wide",),"fields": ("username", "email", "password1", "password2")}),
        ("Información personal", {"classes": ("wide",),"fields": ("first_name","last_name","telefono","direccion","id_documento","fecha_nacimiento")}),
    )
