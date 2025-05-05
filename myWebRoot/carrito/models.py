from django.db import models
from django.conf import settings
from productos.models import Producto

class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Carrito de {self.usuario.username}'
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def cantidad_items(self):
        return self.items.count()

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('carrito', 'producto')
    
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    
    @property
    def subtotal(self):
        return self.cantidad * self.producto.precio