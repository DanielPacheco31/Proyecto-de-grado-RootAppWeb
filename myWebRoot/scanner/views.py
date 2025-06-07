"""Vista de la app scanner."""

import logging
import re

from carrito.models import Carrito, CarritoItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from productos.models import Producto
from usuarios.models import Usuario

# Crear un logger para esta aplicación
logger = logging.getLogger("scanner")

# Constantes para evitar magic numbers
MIN_CODIGO_LENGTH = 3
MAX_CODIGO_LENGTH = 50


def validar_codigo_producto(codigo: str | None) -> tuple[bool, str, str]:
    """Valida que el código del producto tenga un formato válido."""
    if not codigo:
        return False, "", "Código vacío"

    # Limpiar el código
    codigo_limpio = str(codigo).strip().upper()

    # Validar longitud
    if len(codigo_limpio) < MIN_CODIGO_LENGTH:
        return False, codigo_limpio, f"Código muy corto (mínimo {MIN_CODIGO_LENGTH} caracteres)"

    if len(codigo_limpio) > MAX_CODIGO_LENGTH:
        return False, codigo_limpio, f"Código muy largo (máximo {MAX_CODIGO_LENGTH} caracteres)"

    # Validar caracteres permitidos (alfanuméricos y algunos símbolos comunes en códigos)
    patron_valido = re.compile(r"^[A-Z0-9\-_]+$")
    if not patron_valido.match(codigo_limpio):
        return False, codigo_limpio, "Código contiene caracteres no válidos"

    return True, codigo_limpio, ""


def buscar_producto_por_codigo(codigo: str) -> Producto | None:
    """Busca un producto por su código en la base de datos."""
    try:
        # Buscar exacto primero
        producto = Producto.objects.filter(codigo__iexact=codigo).first()

        if not producto:
            # Buscar por códigos similares (sin guiones, espacios, etc.)
            codigo_simple = re.sub(r"[^A-Z0-9]", "", codigo)
            if len(codigo_simple) >= MIN_CODIGO_LENGTH:
                return Producto.objects.filter(
                    codigo__regex=f"^{re.escape(codigo_simple)}$",
                ).first()
            return None  # Si no encontró nada
        return producto
    except Exception:
        logger.exception("Error buscando producto por código %s", codigo)
        return None


def agregar_producto_al_carrito(usuario: Usuario, producto: Producto, cantidad: int = 1) -> tuple[bool, str, CarritoItem | None]:
    """Agrega un producto al carrito del usuario."""
    try:
        with transaction.atomic():
            # Obtener o crear carrito
            carrito, carrito_creado = Carrito.objects.get_or_create(usuario=usuario)

            # Obtener o crear item en el carrito
            item, item_creado = CarritoItem.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={"cantidad": cantidad},
            )

            if not item_creado:
                # Si ya existe, incrementar cantidad
                item.cantidad += cantidad
                item.save()

                return True, f'Cantidad actualizada: {item.cantidad} unidades de "{producto.nombre}"', item
            # Nuevo item agregado
            return True, f'Producto "{producto.nombre}" agregado al carrito', item

    except Exception:
        logger.exception("Error agregando producto %s al carrito del usuario %s", producto.id, usuario.id)
        return False, "Error interno al agregar el producto", None


def _procesar_accion_add(request: HttpRequest, producto: Producto) -> HttpResponse:
    """Procesa la acción de agregar al carrito."""
    exito, mensaje, item = agregar_producto_al_carrito(request.user, producto)

    if exito:
        messages.success(request, mensaje)
        logger.info("Producto '%s' agregado al carrito del usuario %s", producto.nombre, request.user.username)
        return redirect("usuarios:perfil")
    messages.error(request, mensaje)
    return render(request, "scanner/scanner.html")


def _procesar_accion_pay(request: HttpRequest, producto: Producto) -> HttpResponse:
    """Procesa la acción de pagar directamente."""
    exito, mensaje, item = agregar_producto_al_carrito(request.user, producto)

    if exito:
        messages.success(request, f'Producto "{producto.nombre}" listo para pagar')
        logger.info("Producto '%s' agregado para pago directo por usuario %s", producto.nombre, request.user.username)
        return redirect("carrito:finalizar_compra")
    messages.error(request, mensaje)
    return render(request, "scanner/scanner.html")


def _procesar_accion_invalida(request: HttpRequest) -> HttpResponse:
    """Procesa acciones no válidas."""
    messages.error(request, "Acción no válida")
    return render(request, "scanner/scanner.html")


@login_required
def scanner(request: HttpRequest) -> HttpResponse:
    """Función principal del scanner de productos."""
    if request.method == "POST":
        # Obtener datos del formulario
        scanned_code = request.POST.get("scannedCode", "").strip()
        action = request.POST.get("action", "add")

        # Log del intento de escaneo
        logger.info("Código escaneado: '%s' por usuario: %s, acción: %s", scanned_code, request.user.username, action)

        # Validar código
        es_valido, codigo_limpio, error_validacion = validar_codigo_producto(scanned_code)

        if not es_valido:
            messages.error(request, f"Código inválido: {error_validacion}")
            logger.warning("Código inválido '%s' por usuario %s: %s", scanned_code, request.user.username, error_validacion)
            return render(request, "scanner/scanner.html")

        # Buscar producto
        producto = buscar_producto_por_codigo(codigo_limpio)

        if not producto:
            messages.error(request, f'Producto con código "{codigo_limpio}" no encontrado en nuestro sistema')
            logger.info("Producto no encontrado para código '%s' por usuario %s", codigo_limpio, request.user.username)
            return render(request, "scanner/scanner.html")

        # Verificar stock (sin campo activo por ahora)
        if producto.stock is not None and producto.stock <= 0:
            messages.warning(request, f'El producto "{producto.nombre}" está agotado')
            logger.info("Producto agotado '%s' escaneado por usuario %s", producto.nombre, request.user.username)
            return render(request, "scanner/scanner.html")

        # Procesar según la acción
        try:
            if action == "add":
                return _procesar_accion_add(request, producto)
            return _procesar_accion_pay(request, producto) if action == "pay" else _procesar_accion_invalida(request)

        except Exception:
            logger.exception("Error procesando acción '%s' para producto '%s' por usuario %s", action, producto.nombre, request.user.username)
            messages.error(request, "Error procesando la solicitud. Inténtelo nuevamente.")
            return render(request, "scanner/scanner.html")

    # GET request - mostrar página del scanner
    context = {"productos_recientes": obtener_productos_recientes(),"total_productos": Producto.objects.count()}

    return render(request, "scanner/scanner.html", context)


def obtener_productos_recientes() -> QuerySet[Producto]:
    """Obtiene una lista de productos recientes para mostrar como ejemplos."""
    try:
        return Producto.objects.filter(stock__gt=0).order_by("-fecha_creacion")[:5]
    except Exception:
        logger.exception("Error obteniendo productos recientes")
        return Producto.objects.none()
