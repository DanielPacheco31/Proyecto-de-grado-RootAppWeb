from django.contrib.auth.models import User
from django.db import models


class Perfil(models.Model):
    """Clase para traer los datos de los usuarios que se registren."""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    foto = models.ImageField(upload_to="perfiles/", default="perfiles/default.png")
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(blank=True)
    id_documento = models.CharField(max_length=20, blank=True, verbose_name="Documento de identidad")
    preferencias_notificacion = models.BooleanField(default=True, verbose_name="Recibir notificaciones")

    def __str__(self) -> str:
        return f"Perfil de {self.usuario.username}"
