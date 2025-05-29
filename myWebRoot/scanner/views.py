"""Vista de la app scanner."""

import logging

from carrito.models import Carrito, CarritoItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from productos.models import Producto

# Crear un logger para esta aplicación
logger = logging.getLogger("scanner")

@login_required
def scanner(request):
    """Creación de función de scanner."""
    if request.method == "POST":
        scanned_code = request.POST.get("scannedCode", "")
        logger.info(f"Código escaneado: {scanned_code} por usuario: {request.user.username}")
        action = request.POST.get("action", "add")

        if scanned_code:
            # Buscar el producto en la base de datos
            producto = Producto.objects.filter(codigo=scanned_code).first()

            if producto:
                if action == "add":
                    # Lógica para agregar al carrito
                    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

                    item, item_created = CarritoItem.objects.get_or_create(
                        carrito=carrito,
                        producto=producto,
                        defaults={"cantidad": 1},
                    )

                    if not item_created:
                        item.cantidad += 1
                        item.save()

                    messages.success(request, f'Producto "{producto.nombre}" agregado al carrito')
                    return redirect("usuarios:perfil")
                if action == "pay":
                    # Agregar al carrito y redirigir a finalizar compra
                    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

                    item, item_created = CarritoItem.objects.get_or_create(
                        carrito=carrito,
                        producto=producto,
                        defaults={"cantidad": 1},
                    )

                    if not item_created:
                        item.cantidad += 1
                        item.save()

                    messages.success(request, f'Producto "{producto.nombre}" agregado y listo para pagar')
                    return redirect("carrito:finalizar_compra")
            else:
                messages.error(request, f"Producto con código {scanned_code} no encontrado")
                return redirect("scanner:scanner")

    return render(request, "scanner/scanner.html")
