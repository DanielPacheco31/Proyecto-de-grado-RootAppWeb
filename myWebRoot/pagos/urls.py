"""URLs para la aplicación de pagos."""

from django.urls import path

from . import views

app_name = "pagos"


urlpatterns = [
    path("<int:compra_id>/metodo/",views.seleccionar_metodo_pago,name="seleccionar_metodo_pago",),
    path("<int:compra_id>/procesar/", views.procesar_pago, name="procesar_pago"),
    path("transferencia/<int:pago_id>/",views.pago_transferencia,name="pago_transferencia",),
    path("movil/<int:pago_id>/", views.pago_movil, name="pago_movil"),
    path("confirmar/<int:pago_id>/", views.confirmar_pago, name="confirmar_pago"),
]
