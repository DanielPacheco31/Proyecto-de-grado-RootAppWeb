from django.urls import path

from . import views

app_name = "scanner"

urlpatterns = [
    path("", views.scanner, name="scanner"),
]
