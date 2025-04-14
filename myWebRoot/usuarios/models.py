from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    id_documento = models.CharField(max_length=20, blank=True, null=True, verbose_name="Documento de identidad")
    preferencias_notificacion = models.BooleanField(default=True, verbose_name="Recibir notificaciones")
    foto = models.ImageField(upload_to='perfiles/', default='perfiles/default.png')
    
    # Resolver conflictos de accesores inversos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.username

# Crear automáticamente un perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # Verificar si el perfil existe antes de intentar guardarlo
    try:
        instance.perfil.save()
    except User.perfil.RelatedObjectDoesNotExist:
        # Si no existe, creamos uno
        Perfil.objects.create(usuario=instance)
