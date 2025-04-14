from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
import os
from carrito.models import Carrito
from datetime import datetime

# Obtener el modelo de usuario personalizado
User = get_user_model()

def registro_view(request):
    # Si el usuario ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        # Cambiado para usar los nombres de campos correctos de tu HTML
        username = request.POST.get('nombre-usuario')
        email = request.POST.get('correo-electrónico')
        password1 = request.POST.get('contraseña1')
        password2 = request.POST.get('contraseña2')
        
        # Validaciones básicas
        if not username or not email or not password1 or not password2:
            messages.error(request, 'Todos los campos son obligatorios')
            return redirect('usuarios:registro')
            
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('usuarios:registro')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return redirect('usuarios:registro')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return redirect('usuarios:registro')
        
        try:
            # Crear el usuario
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            
            # Ya no necesitamos crear el perfil porque todos los campos están en el modelo User
            
            # Crear carrito para el usuario
            Carrito.objects.create(usuario=user)
            
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            
            # Iniciar sesión automáticamente después del registro
            user = authenticate(request, username=username, password=password1)
            if user:
                login(request, user)
                return redirect('usuarios:perfil')
            else:
                return redirect('usuarios:login')
        
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
            return redirect('usuarios:registro')
    
    return render(request, 'usuarios/registro.html')

def login_view(request):
    # Si el usuario ya está autenticado, redirigir al scanner
    if request.user.is_authenticated:
        return redirect('scanner:scanner')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Si no quiere ser recordado, la sesión expirará al cerrar el navegador
            if not remember:
                request.session.set_expiry(0)
                
            messages.success(request, f'Bienvenido, {username}!')
            
            # Obtener la URL a la que redirigir después del login
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect('scanner:scanner')  # Redirigir al scanner después del login
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)  # Cierra la sesión completamente
    return redirect('core:home')  # Redirige a la página de inicio

@login_required
def perfil_view(request):
    # Usar select_related para reducir consultas a la base de datos
    carrito = Carrito.objects.select_related('usuario').prefetch_related(
        'items__producto'
    ).get_or_create(usuario=request.user)[0]
    
    # Usar prefetch_related para cargar compras y sus detalles en una sola consulta
    compras = request.user.compras.prefetch_related(
        'detalles__producto'
    ).order_by('-fecha_compra')
    
    context = {
        'compras': compras,
        'carrito': carrito
    }
    
    return render(request, 'usuarios/perfil.html', context)

@login_required
def actualizar_perfil(request):
    if request.method == 'POST':
        # Actualizar datos del usuario
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Actualizar datos adicionales directamente en el modelo de usuario
        user.telefono = request.POST.get('telefono', '')
        user.direccion = request.POST.get('direccion', '')
        user.id_documento = request.POST.get('id_documento', '')
        
        fecha_str = request.POST.get('fecha_nacimiento', '')
        if fecha_str:
            try:
                user.fecha_nacimiento = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        user.save()
        
        messages.success(request, 'Perfil actualizado correctamente')
    
    return redirect('usuarios:perfil')

@login_required
def actualizar_foto(request):
    if request.method == 'POST' and request.FILES.get('foto'):
        foto = request.FILES['foto']
        
        # Validar tipo de archivo (imágenes solamente)
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(foto.name)[1].lower()
        
        if ext not in valid_extensions:
            messages.error(request, 'El archivo debe ser una imagen (JPG, PNG o GIF)')
            return redirect('usuarios:perfil')
        
        # Limitar tamaño del archivo (por ejemplo, 5MB)
        if foto.size > 5 * 1024 * 1024:
            messages.error(request, 'La imagen no debe superar los 5MB')
            return redirect('usuarios:perfil')
            
        # Guardar la imagen directamente en el usuario
        user = request.user
        
        # Eliminar foto anterior si no es la predeterminada
        if user.foto and 'default.png' not in user.foto.name:
            if default_storage.exists(user.foto.name):
                default_storage.delete(user.foto.name)
        
        # Generar nombre único para la foto
        filename = f"perfiles/user_{user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
        user.foto.save(filename, ContentFile(foto.read()))
        
        messages.success(request, 'Foto de perfil actualizada correctamente')
    
    return redirect('usuarios:perfil')

@login_required
def actualizar_preferencias(request):
    if request.method == 'POST':
        user = request.user
        user.preferencias_notificacion = 'preferencias_notificacion' in request.POST
        user.save()
        
        messages.success(request, 'Preferencias actualizadas correctamente')
    
    return redirect('usuarios:perfil')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantener la sesión activa después de cambiar la contraseña
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña actualizada correctamente')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('usuarios:perfil')