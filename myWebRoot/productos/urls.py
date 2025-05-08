from django.urls import path

from . import views

app_name = "productos"

urlpatterns = [
    path("", views.lista_productos, name="lista"),
    path("crear/", views.crear_producto, name="crear"),
    path("<int:producto_id>/", views.detalle_producto, name="detalle"),
    path("<int:producto_id>/editar/", views.editar_producto, name="editar"),
    path("<int:producto_id>/eliminar/", views.eliminar_producto, name="eliminar"),
]
