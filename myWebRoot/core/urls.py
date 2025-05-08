from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

app_name = "core"

urlpatterns = [
    path("", cache_page(60 * 60)(views.home_view), name="home"),
    path("vision-mision/", cache_page(60 * 60 * 24)(views.vision_mision), name="vision_mision"),
    path("contacto/", views.contacto, name="contacto"),
]
