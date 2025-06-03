"""Modelos para la aplicacion productos."""

from django.db import models


class Categoria(models.Model):
    """Modelo para categorías de productos."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="")

    class Meta:
        """Metadatos del modelo Categoría."""

        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre


class Producto(models.Model):
    """Modelo para productos."""

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, default="")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    categoria = models.ForeignKey(Categoria,on_delete=models.SET_NULL,blank=True,null=True,related_name="productos")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadatos del modelo Producto."""

        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre
