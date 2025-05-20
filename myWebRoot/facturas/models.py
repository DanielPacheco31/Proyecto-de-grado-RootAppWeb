"""Modelos para la aplicación de facturas."""

import uuid

from django.db import models
from django.utils import timezone


class Factura(models.Model):
    """Modelo para las facturas de las compras.

    Una factura se genera automáticamente cuando se realiza una compra
    y contiene información detallada sobre los productos adquiridos,
    cliente y costos.
    """

    # Usar una referencia de cadena para evitar importaciones circulares
    compra = models.OneToOneField(
        "pagos.Compra",
        on_delete=models.CASCADE,
        related_name="factura",
    )
    numero = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="facturas/", blank=True, null=True)

    def __str__(self) -> str:
        """Representación de cadena de la factura."""
        return f"Factura {self.numero}"

    def save(self, *args: list | tuple, **kwargs: dict) -> None:
        """Guarda la factura y genera un número único si es necesario.

        Args:
            *args: Argumentos posicionales para el método save.
            **kwargs: Argumentos de palabra clave para el método save.

        Returns:
            None

        """
        # Generar número de factura único si es nuevo
        if not self.numero:
            anio = timezone.now().year
            mes = timezone.now().month
            uuid_corto = str(uuid.uuid4())[:8]
            self.numero = f"F-{anio}-{mes:02d}-{uuid_corto}"
        super().save(*args, **kwargs)
