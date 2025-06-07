"""Vistas actualizadas para usar el modelo Usuario personalizado."""
import contextlib
from datetime import datetime
from pathlib import Path

from carrito.models import Carrito
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Usuario  # Cambio importante: usar tu modelo personalizado


def _validar_datos_registro(username: str, email: str, password1: str, password2: str) -> str | None:
    """Valida los datos de registro y retorna error si hay alguno."""
    if not username or not email or not password1 or not password2:
        return "Todos los campos son obligatorios"

    if password1 != password2:
        return "Las contraseñas no coinciden"

    if Usuario.objects.filter(username=username).exists():
        return "El nombre de usuario ya está en uso"

    if Usuario.objects.filter(email=email).exists():
        return "El correo electrónico ya está registrado"

    return None


def _crear_usuario(datos_usuario: dict) -> Usuario:
    """Crea un usuario con los datos proporcionados."""
    user = Usuario.objects.create_user(
        username=datos_usuario["username"],
        email=datos_usuario["email"],
        password=datos_usuario["password1"],
        first_name=datos_usuario["first_name"],
        last_name=datos_usuario["last_name"],
        telefono=datos_usuario["telefono"],
        direccion=datos_usuario["direccion"],
        id_documento=datos_usuario["id_documento"],
    )

    # Convertir y guardar la fecha de nacimiento
    if datos_usuario.get("fecha_nacimiento"):
        try:
            user.fecha_nacimiento = datetime.strptime(datos_usuario["fecha_nacimiento"], "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone()).date()
            user.save()
        except ValueError:
            pass  # Se omite la fecha si hay error

    return user


def registro_view(request: HttpRequest) -> HttpResponse:
    """Vista para el registro de usuarios."""
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        # Obtener datos del formulario
        datos_usuario = {
            "username": request.POST.get("nombre_usuario"),
            "first_name": request.POST.get("nombre"),
            "last_name": request.POST.get("apellido"),
            "email": request.POST.get("correo_electronico"),
            "id_documento": request.POST.get("cedula"),
            "fecha_nacimiento": request.POST.get("fecha_nacimiento"),
            "telefono": request.POST.get("telefono"),
            "direccion": request.POST.get("direccion"),
            "password1": request.POST.get("contraseña1"),
            "password2": request.POST.get("contraseña2"),
        }

        # Validar datos
        error = _validar_datos_registro(
            datos_usuario["username"],
            datos_usuario["email"],
            datos_usuario["password1"],
            datos_usuario["password2"],
        )

        if error:
            messages.error(request, error)
            return redirect("usuarios:registro")

        try:
            # Crear el usuario
            user = _crear_usuario(datos_usuario)

            # Crear carrito para el usuario
            Carrito.objects.create(usuario=user)

            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")

            # Iniciar sesión automáticamente después del registro
            user = authenticate(request, username=datos_usuario["username"], password=datos_usuario["password1"])
            if user:
                login(request, user)
                return redirect("usuarios:perfil")
            return redirect("usuarios:login")

        except (ValueError, TypeError) as e:
            messages.error(request, f"Error al crear el usuario: {e!s}")
            return redirect("usuarios:registro")

    return render(request, "usuarios/registro.html")


def login_view(request: HttpRequest) -> HttpResponse:
    """Una vez el usuario esté autenticado lo redirige al scanner."""
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

            return redirect("scanner:scanner")
        messages.error(request, "Nombre de usuario o contraseña incorrectos")

    return render(request, "usuarios/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    """Cierre de sesión completo."""
    logout(request)
    return redirect("core:home")


@login_required
def perfil_view(request: HttpRequest) -> HttpResponse:
    """Función para la vista del perfil."""
    # Usar select_related para reducir consultas a la base de datos
    carrito = Carrito.objects.select_related("usuario").prefetch_related("items__producto").get_or_create(usuario=request.user)[0]

    # Usar prefetch_related para cargar compras y sus detalles en una sola consulta
    compras = request.user.compras.prefetch_related("detalles__producto").order_by("-fecha_compra")

    context = {"compras": compras,"carrito": carrito}

    return render(request, "usuarios/perfil.html", context)


@login_required
def actualizar_perfil(request: HttpRequest) -> HttpResponse:
    """Actualizaciones de datos del perfil."""
    if request.method == "POST":
        # Actualizar datos del usuario directamente (sin perfil separado)
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.telefono = request.POST.get("telefono", "")
        user.direccion = request.POST.get("direccion", "")
        user.id_documento = request.POST.get("id_documento", "")

        fecha_str = request.POST.get("fecha_nacimiento", "")
        if fecha_str:
            with contextlib.suppress(ValueError):
                user.fecha_nacimiento = datetime.strptime(fecha_str, "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone()).date()

        user.save()

        messages.success(request, "Perfil actualizado correctamente")

    return redirect("usuarios:perfil")


@login_required
def actualizar_foto(request: HttpRequest) -> HttpResponse:
    """Actualización de foto de perfil."""
    if request.method == "POST" and request.FILES.get("foto"):
        foto = request.FILES["foto"]

        # Validar tipo de archivo (imágenes solamente)
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        ext = Path(foto.name).suffix.lower()

        if ext not in valid_extensions:
            messages.error(request, "El archivo debe ser una imagen (JPG, PNG o GIF)")
            return redirect("usuarios:perfil")

        # Limitar tamaño del archivo (por ejemplo, 5MB)
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, "La imagen no debe superar los 5MB")
            return redirect("usuarios:perfil")

        # Guardar la imagen directamente en el usuario
        user = request.user

        # Eliminar foto anterior si no es la predeterminada
        if user.foto and "default.png" not in user.foto.name and default_storage.exists(user.foto.name):
            default_storage.delete(user.foto.name)

        # Generar nombre único para la foto
        filename = f"perfiles/user_{user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
        user.foto.save(filename, ContentFile(foto.read()))

        messages.success(request, "Foto de perfil actualizada correctamente")

    return redirect("usuarios:perfil")


@login_required
def actualizar_preferencias(request: HttpRequest) -> HttpResponse:
    """Actualizaciones de preferencias."""
    if request.method == "POST":
        user = request.user
        user.preferencias_notificacion = "preferencias_notificacion" in request.POST
        user.save()

        messages.success(request, "Preferencias actualizadas correctamente")

    return redirect("usuarios:perfil")


@login_required
def cambiar_password(request: HttpRequest) -> HttpResponse:
    """Esta función fue creada para que por seguridad el usuario cambie su contraseña."""
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
