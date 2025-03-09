from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    return render(request,"home.html")

def home_view(request):
    if request.method == 'POST':
        scanned_code = request.POST.get('scannedCode', '')
        if scanned_code:
            # Aquí puedes buscar el producto en tu base de datos
            # Ejemplo: producto = Producto.objects.filter(codigo=scanned_code).first()
            
            # Si encuentras el producto, puedes añadirlo al carrito o mostrarlo
            messages.success(request, f'Producto con código {scanned_code} escaneado correctamente')
            # return redirect('detalle_producto', codigo=scanned_code)
    
    return render(request, 'home.html')  # Tu plantilla actual

def vision_mision(request):
    return render(request, 'visionMision.html')

def scanner_view(request):
    return HttpResponse("¡Hola desde scanner_view!")

def registro_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validaciones básicas
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registro')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return redirect('registro')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return redirect('registro')
        
        # Crear el usuario
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        
        messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
        return redirect('login')
    
    return render(request, 'registro.html')

def login_view(request):
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
            return redirect('home')  # Redirigir a la página principal después del login
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

def contacto(request):
    return render(request, 'contacto.html')

@login_required
def scanner(request):
    return render(request, 'scanner.html')

def enviar_contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        empresa = request.POST.get('empresa', '')
        mensaje = request.POST.get('mensaje')
        
        # Aquí puedes procesar el formulario de contacto
        # Por ejemplo, enviar un correo electrónico o guardar en la base de datos
        
        messages.success(request, '¡Gracias por contactarnos! Nos pondremos en contacto contigo pronto.')
        return redirect('contacto')
    
    return redirect('contacto')

