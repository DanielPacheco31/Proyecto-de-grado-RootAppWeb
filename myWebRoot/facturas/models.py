"""Modelos para la aplicación de facturas."""

from typing import ClassVar

from django.db import models


class Factura(models.Model):
    """
    Modelo para las facturas de las compras.

    Una factura se genera automáticamente cuando se realiza una compra
    y contiene información detallada sobre los productos adquiridos,
    cliente y costos.
    """

    # Usar una referencia de cadena para evitar importaciones circulares
    compra = models.OneToOneField("pagos.Compra", on_delete=models.CASCADE, related_name="factura")
    numero = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="facturas/", blank=True, null=True)

    class Meta:
        """Metadatos del modelo Factura."""

        ordering: ClassVar[list[str]] = ["-fecha_emision"]
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    def __str__(self) -> str:
        """Representación de cadena de la factura."""
        return f"Factura {self.numero}"
