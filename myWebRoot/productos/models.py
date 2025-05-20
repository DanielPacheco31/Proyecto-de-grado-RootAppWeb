import os

from django.db import models
from django.utils.text import slugify


def producto_imagen_path(instance: str, filename: str) -> str:
    """Define la ruta donde se guardará la imagen del producto."""
    # Obtener la extensión del archivo
    ext = filename.split(".")[-1]
    # Generar un nombre de archivo basado en el nombre del producto
    nombre_archivo = f"{slugify(instance.nombre)}.{ext}"
    # Devolver la ruta
    return os.path.join("productos", nombre_archivo)


class Categoria(models.Model):
    """Modelo para categorías de productos."""

    class Meta:
        """Metadatos del modelo Categoría."""

        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre


class Producto(models.Model):
    """Modelo para productos."""

    # Constante para umbral de stock bajo
    UMBRAL_STOCK_BAJO = 10

    class Meta:
        """Metadatos del modelo Producto."""

        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, default="")  # Reemplazamos null=True por default=""
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to=producto_imagen_path, blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="productos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre

    @property
    def tiene_stock(self) -> bool:
        """Verifica si el producto tiene stock disponible."""
        return self.stock > 0

    @property
    def estado_stock(self) -> str:
        """Retorna un estado del stock para usar en la interfaz."""
        if self.stock <= 0:
            return "sin_stock"
        if self.stock < self.UMBRAL_STOCK_BAJO:
            return "stock_bajo"
        return "stock_disponible"

    @property
    def texto_estado_stock(self) -> str:
        """Retorna un texto descriptivo del estado del stock."""
        estados = {
            "sin_stock": "Sin stock",
            "stock_bajo": f"Bajo stock ({self.stock})",
            "stock_disponible": f"En stock ({self.stock})",
        }
        return estados.get(self.estado_stock, "Desconocido")
