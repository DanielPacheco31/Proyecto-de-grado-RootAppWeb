"""Vistas para la aplicación principal de ROOT."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def home_view(request: HttpRequest) -> HttpResponse:
    """
    Renderiza la página de inicio.

    Args:
        request: La solicitud HTTP.

    Returns:
        HttpResponse: La página de inicio renderizada.

    """
    return render(request, "core/home.html")


def vision_mision(request: HttpRequest) -> HttpResponse:
    """
    Renderiza la página de visión y misión de la empresa.

    Args:
        request: La solicitud HTTP.

    Returns:
        HttpResponse: La página de visión y misión renderizada.

    """
    return render(request, "core/visionMision.html")


def contacto(request: HttpRequest) -> HttpResponse:
    """
    Maneja el formulario de contacto y renderiza la página de contacto.

    Procesa los datos del formulario cuando se envía por POST y muestra un mensaje
    de confirmación. En las solicitudes GET, simplemente muestra el formulario.

    Args:
        request: La solicitud HTTP.

    Returns:
        HttpResponse: La página de contacto renderizada o redirección tras envío.

    """
    if request.method == "POST":
        request.POST.get("nombre")
        request.POST.get("email")
        request.POST.get("empresa", "")
        request.POST.get("mensaje")

        # Aqui puedes procesar el formulario de contacto
        # Por ejemplo, enviar un correo electronico o guardar en la base de datos

        messages.success(
            request,
            "¡Gracias por contactarnos! Nos pondremos en contacto contigo pronto.",
        )
        return redirect("core:contacto")

    return render(request, "core/contacto.html")
