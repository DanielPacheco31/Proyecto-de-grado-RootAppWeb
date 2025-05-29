"""Vista de la app scanner."""

import logging
import re

from carrito.models import Carrito, CarritoItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db import transaction
from productos.models import Producto

# Crear un logger para esta aplicación
logger = logging.getLogger("scanner")


def validar_codigo_producto(codigo):
    """
    Valida que el código del producto tenga un formato válido.
    
    Args:
        codigo (str): Código a validar
        
    Returns:
        tuple: (es_valido, codigo_limpio, mensaje_error)
    """
    if not codigo:
        return False, "", "Código vacío"
    
    # Limpiar el código
    codigo_limpio = str(codigo).strip().upper()
    
    # Validar longitud
    if len(codigo_limpio) < 3:
        return False, codigo_limpio, "Código muy corto (mínimo 3 caracteres)"
    
    if len(codigo_limpio) > 50:
        return False, codigo_limpio, "Código muy largo (máximo 50 caracteres)"
    
    # Validar caracteres permitidos (alfanuméricos y algunos símbolos comunes en códigos)
    patron_valido = re.compile(r'^[A-Z0-9\-_]+$')
    if not patron_valido.match(codigo_limpio):
        return False, codigo_limpio, "Código contiene caracteres no válidos"
    
    return True, codigo_limpio, ""


def buscar_producto_por_codigo(codigo):
    """
    Busca un producto por su código en la base de datos.
    
    Args:
        codigo (str): Código del producto
        
    Returns:
        Producto or None: Producto encontrado o None
    """
    try:
        # Buscar exacto primero
        producto = Producto.objects.filter(codigo__iexact=codigo).first()
        
        if not producto:
            # Buscar por códigos similares (sin guiones, espacios, etc.)
            codigo_simple = re.sub(r'[^A-Z0-9]', '', codigo)
            if len(codigo_simple) >= 3:
                producto = Producto.objects.filter(
                    codigo__regex=f'^{re.escape(codigo_simple)}$'
                ).first()
        
        return producto
    except Exception as e:
        logger.error(f"Error buscando producto por código {codigo}: {e}")
        return None


def agregar_producto_al_carrito(usuario, producto, cantidad=1):
    """
    Agrega un producto al carrito del usuario.
    
    Args:
        usuario: Usuario propietario del carrito
        producto: Producto a agregar
        cantidad: Cantidad a agregar (default 1)
        
    Returns:
        tuple: (exito, mensaje, item_carrito)
    """
    try:
        with transaction.atomic():
            # Obtener o crear carrito
            carrito, carrito_creado = Carrito.objects.get_or_create(usuario=usuario)
            
            # Obtener o crear item en el carrito
            item, item_creado = CarritoItem.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={"cantidad": cantidad}
            )
            
            if not item_creado:
                # Si ya existe, incrementar cantidad
                item.cantidad += cantidad
                item.save()
                
                return True, f'Cantidad actualizada: {item.cantidad} unidades de "{producto.nombre}"', item
            else:
                # Nuevo item agregado
                return True, f'Producto "{producto.nombre}" agregado al carrito', item
                
    except Exception as e:
        logger.error(f"Error agregando producto {producto.id} al carrito del usuario {usuario.id}: {e}")
        return False, f"Error interno al agregar el producto: {str(e)}", None


@login_required
def scanner(request):
    """Función principal del scanner de productos."""
    
    if request.method == "POST":
        # Obtener datos del formulario
        scanned_code = request.POST.get("scannedCode", "").strip()
        action = request.POST.get("action", "add")
        
        # Log del intento de escaneo
        logger.info(f"Código escaneado: '{scanned_code}' por usuario: {request.user.username}, acción: {action}")
        
        # Validar código
        es_valido, codigo_limpio, error_validacion = validar_codigo_producto(scanned_code)
        
        if not es_valido:
            messages.error(request, f"Código inválido: {error_validacion}")
            logger.warning(f"Código inválido '{scanned_code}' por usuario {request.user.username}: {error_validacion}")
            return render(request, "scanner/scanner.html")
        
        # Buscar producto
        producto = buscar_producto_por_codigo(codigo_limpio)
        
        if not producto:
            messages.error(request, f'Producto con código "{codigo_limpio}" no encontrado en nuestro sistema')
            logger.info(f"Producto no encontrado para código '{codigo_limpio}' por usuario {request.user.username}")
            return render(request, "scanner/scanner.html")
        
        # Verificar stock (sin campo activo por ahora)
        if producto.stock is not None and producto.stock <= 0:
            messages.warning(request, f'El producto "{producto.nombre}" está agotado')
            logger.info(f"Producto agotado '{producto.nombre}' escaneado por usuario {request.user.username}")
            return render(request, "scanner/scanner.html")
        
        # Procesar según la acción
        try:
            if action == "add":
                # Agregar al carrito
                exito, mensaje, item = agregar_producto_al_carrito(request.user, producto)
                
                if exito:
                    messages.success(request, mensaje)
                    logger.info(f"Producto '{producto.nombre}' agregado al carrito del usuario {request.user.username}")
                    return redirect("usuarios:perfil")
                else:
                    messages.error(request, mensaje)
                    return render(request, "scanner/scanner.html")
                    
            elif action == "pay":
                # Agregar al carrito y redirigir a pago
                exito, mensaje, item = agregar_producto_al_carrito(request.user, producto)
                
                if exito:
                    messages.success(request, f'Producto "{producto.nombre}" listo para pagar')
                    logger.info(f"Producto '{producto.nombre}' agregado para pago directo por usuario {request.user.username}")
                    return redirect("carrito:finalizar_compra")
                else:
                    messages.error(request, mensaje)
                    return render(request, "scanner/scanner.html")
            else:
                messages.error(request, "Acción no válida")
                return render(request, "scanner/scanner.html")
                
        except Exception as e:
            logger.error(f"Error procesando acción '{action}' para producto '{producto.nombre}' por usuario {request.user.username}: {e}")
            messages.error(request, "Error procesando la solicitud. Inténtelo nuevamente.")
            return render(request, "scanner/scanner.html")
    
    # GET request - mostrar página del scanner
    context = {
        'productos_recientes': obtener_productos_recientes(),
        'total_productos': Producto.objects.count(),
    }
    
    return render(request, "scanner/scanner.html", context)


def obtener_productos_recientes():
    """
    Obtiene una lista de productos recientes para mostrar como ejemplos.
    
    Returns:
        QuerySet: Productos recientes
    """
    try:
        return Producto.objects.filter(stock__gt=0).order_by('-fecha_creacion')[:5]
    except Exception as e:
        logger.error(f"Error obteniendo productos recientes: {e}")
        return Producto.objects.none()
