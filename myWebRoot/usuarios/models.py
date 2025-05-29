"""Modelos de la app usuarios."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class Usuario(AbstractUser):
    """Modelo de usuario personalizado que extiende AbstractUser."""
    
    foto = models.ImageField(
        upload_to="perfiles/", 
        default="perfiles/default.png",
        verbose_name="Foto de perfil"
    )
    telefono = models.CharField(
        max_length=15, 
        blank=True,
        verbose_name="Teléfono"
    )
    direccion = models.TextField(
        blank=True,
        verbose_name="Dirección"
    )
    fecha_nacimiento = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Fecha de nacimiento"
    )
    id_documento = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Documento de identidad"
    )
    preferencias_notificacion = models.BooleanField(
        default=True, 
        verbose_name="Recibir notificaciones"
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username