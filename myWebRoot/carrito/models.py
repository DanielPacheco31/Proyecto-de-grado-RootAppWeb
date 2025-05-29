"""Modelos para la aplicación de carrito de compras."""

from django.conf import settings
from django.db import models
from productos.models import Producto


class Carrito(models.Model):
    """
    Modelo para almacenar el carrito de compras de un usuario.

    Un carrito está vinculado a un usuario específico y contiene una colección
    de items (productos) que el usuario desea comprar.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Cambio principal aquí
        on_delete=models.CASCADE,
        related_name="carrito",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Representación de cadena del carrito."""
        return f"Carrito de {self.usuario.username}"

    @property
    def total(self):
        """Calcula el total del carrito."""
        return sum(item.cantidad * item.producto.precio for item in self.items.all())


class CarritoItem(models.Model):
    """
    Modelo para almacenar cada producto añadido al carrito.

    Cada item está asociado a un carrito específico y representa una cantidad
    determinada de un producto.
    """

    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadatos del modelo CarritoItem."""

        unique_together = ("carrito", "producto")

    def __str__(self) -> str:
        """Representación de cadena del item en el carrito."""
        return f"{self.cantidad} x {self.producto.nombre}"
        