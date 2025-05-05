from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('telefono', 'direccion', 'fecha_nacimiento', 'id_documento', 'preferencias_notificacion', 'foto')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('telefono', 'direccion', 'fecha_nacimiento', 'id_documento', 'preferencias_notificacion', 'foto')}),
    )

admin.site.register(User, CustomUserAdmin)