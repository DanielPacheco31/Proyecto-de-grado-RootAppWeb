"""Rutas de los usuarios."""

from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.registro_view, name="registro"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/", views.perfil_view, name="perfil"),
    path("perfil/actualizar/", views.actualizar_perfil, name="actualizar_perfil"),
    path("perfil/actualizar-foto/", views.actualizar_foto, name="actualizar_foto"),
    path("perfil/preferencias/", views.actualizar_preferencias, name="actualizar_preferencias"),
    path("perfil/cambiar-password/", views.cambiar_password, name="cambiar_password"),
]
