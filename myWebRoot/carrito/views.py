"""Vistas para la aplicación de carrito de compras."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from pagos.models import Compra, DetalleCompra
from productos.models import Producto

from .models import Carrito, CarritoItem


@login_required
def finalizar_compra(request: HttpRequest) -> HttpResponse:
    """Finaliza la compra de los productos en el carrito del usuario."""
    # Usar select_related para cargar usuario en una sola consulta
    try:
        carrito = Carrito.objects.select_related("usuario").prefetch_related("items__producto").get(usuario=request.user)
    except Carrito.DoesNotExist:
        messages.error(request, "No tienes un carrito activo")
        return redirect("usuarios:perfil")

    if not carrito.items.exists():
        messages.error(request, "El carrito está vacío")
        return redirect("usuarios:perfil")

    if request.method == "POST":
        direccion_entrega = request.POST.get("direccion_entrega")

        # Usar transaction.atomic para garantizar que toda la operación sea atómica
        with transaction.atomic():
            # Obtener dirección de entrega del usuario si no se proporciona
            usuario_direccion = request.user.direccion or ""

            compra = Compra.objects.create(usuario=request.user, estado="pendiente", total=carrito.total, direccion_entrega=direccion_entrega or usuario_direccion)

            # Crear todos los detalles de compra de una vez en lugar de uno por uno
            detalles_compra = []
            productos_actualizar = []

            for item in carrito.items.select_related("producto").all():
                detalles_compra.append(DetalleCompra(compra=compra, producto=item.producto, cantidad=item.cantidad, precio_unitario=item.producto.precio))

                # Actualizar stock
                producto = item.producto
                producto.stock = max(0, producto.stock - item.cantidad)
                productos_actualizar.append(producto)

            # Crear todos los detalles en una sola operación
            DetalleCompra.objects.bulk_create(detalles_compra)

            # Actualizar todos los productos en una sola operación
            Producto.objects.bulk_update(productos_actualizar, ["stock"])

            # Eliminar todos los items del carrito en una sola operación
            carrito.items.all().delete()

        messages.success(request, "Compra realizada con éxito")
        # Redirigir a la selección de método de pago
        return redirect("pagos:seleccionar_metodo_pago", compra_id=compra.id)

    return render(request, "carrito/checkout.html", {"carrito": carrito})


@login_required
def actualizar_cantidad(request: HttpRequest, item_id: int) -> HttpResponse:
    """Actualiza la cantidad de un producto en el carrito."""
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "sumar":
            # Verificar stock disponible antes de aumentar
            if item.cantidad < item.producto.stock:
                item.cantidad += 1
                item.save()
            else:
                messages.warning(request, f"No hay suficiente stock de {item.producto.nombre}")
        elif accion == "restar" and item.cantidad > 1:
            item.cantidad -= 1
            item.save()

    return redirect("usuarios:perfil")


@login_required
def eliminar_item(request: HttpRequest, item_id: int) -> HttpResponse:
    """Elimina un producto del carrito de forma segura."""
    if request.method == "POST":
        try:
            item = CarritoItem.objects.select_related("producto").get(id=item_id, carrito__usuario=request.user)
            producto_nombre = item.producto.nombre
            item.delete()
            messages.success(request, f"'{producto_nombre}' eliminado del carrito")

        except CarritoItem.DoesNotExist:
            messages.info(request, "El producto ya no está disponible en tu carrito")

        except (ValueError, TypeError, AttributeError):
            messages.error(request, "Ocurrió un error al eliminar el producto")

    return redirect("usuarios:perfil")
