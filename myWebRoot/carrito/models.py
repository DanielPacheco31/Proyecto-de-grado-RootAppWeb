"""Modelos para la aplicación de carrito de compras."""

from django.contrib.auth.models import User
from django.db import models
from productos.models import Producto


class Carrito(models.Model):
    """Modelo para almacenar el carrito de compras de un usuario.

    Un carrito está vinculado a un usuario específico y contiene una colección
    de items (productos) que el usuario desea comprar.
    """

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="carrito",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Representación de cadena del carrito."""
        return f"Carrito de {self.usuario.username}"

    @property
    def total(self) -> float:
        """Calcula el valor total de todos los items en el carrito.

        Returns:
            float: Suma de los subtotales de todos los items.

        """
        return sum(item.subtotal for item in self.items.all())

    @property
    def cantidad_items(self) -> int:
        """Cuenta el número total de items en el carrito.

        Returns:
            int: Número de items en el carrito.

        """
        return self.items.count()


class CarritoItem(models.Model):
    """Modelo para almacenar cada producto añadido al carrito.

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

    @property
    def subtotal(self) -> float:
        """Calcula el valor total de este item (cantidad * precio unitario).

        Returns:
            float: Subtotal del item.

        """
        return self.cantidad * self.producto.precio
