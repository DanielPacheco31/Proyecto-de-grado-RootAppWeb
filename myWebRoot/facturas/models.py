import uuid

from django.db import models
from django.utils import timezone


class Factura(models.Model):
    # Usar una referencia de cadena para evitar importaciones circulares
    compra = models.OneToOneField("pagos.Compra", on_delete=models.CASCADE, related_name="factura")
    numero = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="facturas/", blank=True, null=True)

    def __str__(self) -> str:
        return f"Factura {self.numero}"

    def save(self, *args, **kwargs) -> None:
        # Generar número de factura único si es nuevo
        if not self.numero:
            año = timezone.now().year
            mes = timezone.now().month
            # Formato: F-AÑO-MES-UUID
            uuid_corto = str(uuid.uuid4())[:8]
            self.numero = f"F-{año}-{mes:02d}-{uuid_corto}"
        super().save(*args, **kwargs)
