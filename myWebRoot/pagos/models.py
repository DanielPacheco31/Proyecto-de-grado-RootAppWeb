"""Modelos para la aplicación de pagos."""

from django.conf import settings
from django.db import models
from productos.models import Producto


class Compra(models.Model):
    """Modelo para registrar las compras de los usuarios."""

    ESTADO_CHOICES = (("pendiente", "Pendiente"),("pagado", "Pagado"),("enviado", "Enviado"),("entregado", "Entregado"),("cancelado", "Cancelado"),)

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="compras")
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default="pendiente",)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_entrega = models.TextField(blank=True, default="")
    codigo_seguimiento = models.CharField(max_length=50, blank=True, default="")

    def __str__(self) -> str:
        """Representación de cadena del objeto Compra."""
        return f"Compra {self.id} - {self.usuario.username}"


class DetalleCompra(models.Model):
    """Modelo para registrar los productos incluidos en una compra."""

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles",)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        """Representación de cadena del objeto DetalleCompra."""
        return f"{self.cantidad} x {self.producto.nombre}"

    @property
    def subtotal(self):
        """Calcula el subtotal del detalle de compra."""
        return self.cantidad * self.precio_unitario


class MetodoPago(models.Model):
    """Modelo para definir los métodos de pago disponibles."""

    TIPO_CHOICES = (("nequi", "Nequi"),("bancolombia", "Bancolombia"),("pse", "PSE"),("tarjeta", "Tarjeta de Crédito"),("movil", "Pago Móvil"),("transferencia", "Transferencia Bancaria"),)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    activo = models.BooleanField(default=True)
    configuracion = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        """Representación de cadena del objeto MetodoPago."""
        return self.nombre


class Pago(models.Model):
    """Modelo para registrar los pagos realizados por cada compra."""

    ESTADO_CHOICES = (("pendiente", "Pendiente"),("pagado", "Pagado"),("cancelado", "Cancelado"),)
    compra = models.OneToOneField(Compra,on_delete=models.CASCADE,related_name="pago",)
    metodo_pago = models.ForeignKey(MetodoPago,on_delete=models.PROTECT,related_name="pagos",)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=100, blank=True, default="")
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default="pendiente",)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Representación de cadena del objeto Pago."""
        return f"Pago {self.id} - {self.compra.id}"
        