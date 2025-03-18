from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Actualizado para usar home_view como función principal
def home_view(request):
    if request.method == 'POST':
        scanned_code = request.POST.get('scannedCode', '')
        if scanned_code:
            # Aquí puedes buscar el producto en tu base de datos
            # Ejemplo: producto = Producto.objects.filter(codigo=scanned_code).first()
            
            # Si encuentras el producto, puedes añadirlo al carrito o mostrarlo
            messages.success(request, f'Producto con código {scanned_code} escaneado correctamente')
            # return redirect('detalle_producto', codigo=scanned_code)
    
    return render(request, 'home.html')

# Alias para compatibilidad con urls existentes
def home(request):
    return home_view(request)

def vision_mision(request):
    return render(request, 'visionMision.html')

def contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        empresa = request.POST.get('empresa', '')
        mensaje = request.POST.get('mensaje')
        
        # Aquí puedes procesar el formulario de contacto
        # Por ejemplo, enviar un correo electrónico o guardar en la base de datos
        
        messages.success(request, '¡Gracias por contactarnos! Nos pondremos en contacto contigo pronto.')
        return redirect('contacto')
    
    return render(request, 'contacto.html')

def registro_view(request):
    # Si el usuario ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        # Cambiado para usar los nombres de campos correctos de tu HTML
        username = request.POST.get('nombre-usuario')
        email = request.POST.get('correo-electrónico')
        password1 = request.POST.get('contraseña1')
        password2 = request.POST.get('contraseña2')
        
        # Validaciones básicas
        if not username or not email or not password1 or not password2:
            messages.error(request, 'Todos los campos son obligatorios')
            return redirect('registro')
            
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registro')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return redirect('registro')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return redirect('registro')
        
        try:
            # Crear el usuario
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            
            # Iniciar sesión automáticamente después del registro
            user = authenticate(request, username=username, password=password1)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {username}!')
                return redirect('scanner')  # Redirigir al scanner después del registro
                
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
            return redirect('registro')
    
    return render(request, 'registro.html')

def login_view(request):
    # Si el usuario ya está autenticado, redirigir al scanner
    if request.user.is_authenticated:
        return redirect('scanner')
        
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
            
            return redirect('scanner')  # Redirigir al scanner después del login
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('home')

@login_required
def perfil_view(request):
    return render(request, 'perfil.html')

# Elimino scanner_view duplicado y me quedo con scanner decorado con login_required
@login_required
def scanner(request):
    return render(request, 'scanner.html')

# Alias para compatibilidad con urls existentes
def scanner_view(request):
    return scanner(request)
