"""URLs para la aplicación de carrito de compras."""

from django.urls import path

from . import views

app_name = "carrito"

urlpatterns = [
    path("actualizar/<int:item_id>/", views.actualizar_cantidad,name="actualizar_cantidad"),
    path("eliminar/<int:item_id>/", views.eliminar_item, name="eliminar_item"),
    path("finalizar/", views.finalizar_compra, name="finalizar_compra"),
]
