from django.contrib import messages
from django.shortcuts import redirect, render


def home_view(request):
    return render(request, "core/home.html")

def vision_mision(request):
    return render(request, "core/visionMision.html")

def contacto(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        empresa = request.POST.get("empresa", "")
        mensaje = request.POST.get("mensaje")

        # Aqui puedes procesar el formulario de contacto
        # Por ejemplo, enviar un correo electronico o guardar en la base de datos

        messages.success(request, "¡Gracias por contactarnos! Nos pondremos en contacto contigo pronto.")
        return redirect("core:contacto")

    return render(request, "core/contacto.html")
