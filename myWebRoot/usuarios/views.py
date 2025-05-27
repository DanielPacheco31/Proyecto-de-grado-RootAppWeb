import contextlib
import os
from datetime import datetime

from carrito.models import Carrito
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone


def registro_view(request: HttpRequest) -> HttpResponse:
    """Vista para el registro de usuarios."""
    if request.user.is_authenticated:  # Si el usuario ya está autenticado, redirigir al home
        return redirect("core:home")

    if request.method == "POST":
        # Obtener datos del formulario usando los nombres correctos de tu HTML
        username = request.POST.get("nombre_usuario")
        first_name = request.POST.get("nombre")
        last_name = request.POST.get("apellido")
        email = request.POST.get("correo_electronico")
        id_documento = request.POST.get("cedula")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        telefono = request.POST.get("telefono")
        direccion = request.POST.get("direccion")
        password1 = request.POST.get("contraseña1")
        password2 = request.POST.get("contraseña2")

        # Validaciones básicas
        if not username or not email or not password1 or not password2:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("usuarios:registro")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect("usuarios:registro")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso")
            return redirect("usuarios:registro")

        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está registrado")
            return redirect("usuarios:registro")

        try:
            # Crear el usuario con nombre y apellido
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )

            # Actualizar el perfil con los datos adicionales
            perfil = user.perfil  # El perfil se crea automáticamente gracias a tus señales
            perfil.id_documento = id_documento
            perfil.telefono = telefono
            perfil.direccion = direccion

            # Convertir y guardar la fecha de nacimiento
            if fecha_nacimiento:
                try:
                    perfil.fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
                except ValueError:
                    messages.warning(request, "Formato de fecha de nacimiento inválido. Se omitió este campo.")

            # Guardar el perfil con los cambios
            perfil.save()

            # Crear carrito para el usuario
            Carrito.objects.create(usuario=user)

            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")

            # Iniciar sesión automáticamente después del registro
            user = authenticate(request, username=username, password=password1)
            if user:
                login(request, user)
                return redirect("usuarios:perfil")
            return redirect("usuarios:login")

        except Exception as e:
            messages.error(request, f"Error al crear el usuario: {e!s}")
            return redirect("usuarios:registro")

    return render(request, "usuarios/registro.html")

def login_view(request: HttpRequest) -> HttpResponse:
    """Una vez el usuario este autenticado lo redirije al scanner."""
    if request.user.is_authenticated:
        return redirect("scanner:scanner")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Si no quiere ser recordado, la sesión expirará al cerrar el navegador
            if not remember:
                request.session.set_expiry(0)

            messages.success(request, f"Bienvenido, {username}!")

            # Obtener la URL a la que redirigir después del login
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("scanner:scanner")  # Redirigir al scanner después del login
        messages.error(request, "Nombre de usuario o contraseña incorrectos")

    return render(request, "usuarios/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    """Cierre de sesion completo."""
    logout(request)
    return redirect("core:home")

@login_required
def perfil_view(request: HttpRequest) -> HttpResponse:
    """Funcion para la vista del perfil."""
    # Usar select_related para reducir consultas a la base de datos
    carrito = Carrito.objects.select_related("usuario").prefetch_related(
        "items__producto",
    ).get_or_create(usuario=request.user)[0]

    # Usar prefetch_related para cargar compras y sus detalles en una sola consulta
    compras = request.user.compras.prefetch_related(
        "detalles__producto",
    ).order_by("-fecha_compra")

    context = {
        "compras": compras,
        "carrito": carrito,
    }

    return render(request, "usuarios/perfil.html", context)

@login_required
def actualizar_perfil(request: HttpRequest) -> HttpResponse:
    """Actualizaciones de datos del perfil."""
    if request.method == "POST":
        # Actualizar datos del usuario
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()

        # Actualizar datos del perfil
        perfil = user.perfil
        perfil.telefono = request.POST.get("telefono", "")
        perfil.direccion = request.POST.get("direccion", "")
        perfil.id_documento = request.POST.get("id_documento", "")

        fecha_str = request.POST.get("fecha_nacimiento", "")
        if fecha_str:
            with contextlib.suppress(ValueError):
                perfil.fecha_nacimiento = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        perfil.save()

        messages.success(request, "Perfil actualizado correctamente")

    return redirect("usuarios:perfil")

@login_required
def actualizar_foto(request: HttpRequest) -> HttpResponse:
    """Actulizacion de foto de perfil."""
    if request.method == "POST" and request.FILES.get("foto"):
        foto = request.FILES["foto"]

        # Validar tipo de archivo (imágenes solamente)
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        ext = os.path.splitext(foto.name)[1].lower()

        if ext not in valid_extensions:
            messages.error(request, "El archivo debe ser una imagen (JPG, PNG o GIF)")
            return redirect("usuarios:perfil")

        # Limitar tamaño del archivo (por ejemplo, 5MB)
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, "La imagen no debe superar los 5MB")
            return redirect("usuarios:perfil")

        # Guardar la imagen
        perfil = request.user.perfil

        # Eliminar foto anterior si no es la predeterminada
        if perfil.foto and "default.png" not in perfil.foto.name and default_storage.exists(perfil.foto.name):
            default_storage.delete(perfil.foto.name)

        # Generar nombre único para la foto
        filename = f"perfiles/user_{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
        perfil.foto.save(filename, ContentFile(foto.read()))

        messages.success(request, "Foto de perfil actualizada correctamente")

    return redirect("usuarios:perfil")

@login_required
def actualizar_preferencias(request: HttpRequest) -> HttpResponse:
    """Acualizaciones de seguridad."""
    if request.method == "POST":
        perfil = request.user.perfil
        perfil.preferencias_notificacion = "preferencias_notificacion" in request.POST
        perfil.save()

        messages.success(request, "Preferencias actualizadas correctamente")

    return redirect("usuarios:perfil")

@login_required
def cambiar_password(request: HttpRequest) -> HttpResponse:
    """Esta funcion fue creada para que por seguridad el usuario cambie su contraseña."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantener la sesión activa después de cambiar la contraseña
            update_session_auth_hash(request, user)
            messages.success(request, "Contraseña actualizada correctamente")
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect("usuarios:perfil")
