"""URLs para la aplicación de facturas."""

from django.urls import path

from . import views

app_name = "facturas"

urlpatterns = [
    path("<int:compra_id>/", views.detalle_compra, name="detalle_compra"),
    path("<int:compra_id>/descargar/",views.descargar_factura,name="descargar_factura"),
    path("<int:compra_id>/cancelar/", views.cancelar_compra, name="cancelar_compra"),
]
