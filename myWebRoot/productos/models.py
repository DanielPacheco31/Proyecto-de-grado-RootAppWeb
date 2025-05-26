""""Modelos para la aplicacion productos."""

from django.db import models


class Categoria(models.Model):
    """Modelo para categorías de productos."""

    class Meta:
        """Metadatos del modelo Categoría."""

        nombre = models.CharField(max_length=100)
        descripcion = models.TextField(blank=True, default="")

        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre


class Producto(models.Model):
    """Modelo para productos."""

    class Meta:
        """Metadatos del modelo Producto."""

        nombre = models.CharField(max_length=200)
        codigo = models.CharField(max_length=50, unique=True)
        descripcion = models.TextField(blank=True, default="")
        precio = models.DecimalField(max_digits=10, decimal_places=2)
        stock = models.PositiveIntegerField(default=0)
        categoria = models.ForeignKey(Categoria,on_delete=models.SET_NULL,blank=True,null=True,related_name="productos")
        fecha_creacion = models.DateTimeField(auto_now_add=True)
        fecha_actualizacion = models.DateTimeField(auto_now=True)

        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self) -> str:
        """Representación en cadena del objeto."""
        return self.nombre
