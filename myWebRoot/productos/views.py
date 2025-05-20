"""Vistas para la aplicación de productos."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Categoria, Producto


@login_required
def lista_productos(request: HttpRequest) -> HttpResponse:
    """Lista de todos los productos."""
    productos = Producto.objects.all().order_by("-id")

    # Filtrar por nombre si se proporciona en la búsqueda
    busqueda = request.GET.get("busqueda", "")
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    # Filtrar por categoría si se proporciona
    categoria_id = request.GET.get("categoria", "")
    if categoria_id and categoria_id.isdigit():
        productos = productos.filter(categoria__id=categoria_id)

    categorias = Categoria.objects.all()

    return render(request, "productos/lista_productos.html", {
        "productos": productos,
        "categorias": categorias,
        "busqueda": busqueda,
        "categoria_seleccionada": categoria_id,
    })


@login_required
def detalle_producto(request: HttpRequest, producto_id: int) -> HttpResponse:
    """Detalle de un producto específico."""
    producto = get_object_or_404(Producto, id=producto_id)

    return render(request, "productos/detalle_producto.html", {
        "producto": producto,
    })


@login_required
def crear_producto(request: HttpRequest) -> HttpResponse:
    """Crear un nuevo producto."""
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.POST.get("nombre")
        codigo = request.POST.get("codigo")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        descripcion = request.POST.get("descripcion")
        categoria_id = request.POST.get("categoria")
        imagen = request.FILES.get("imagen")

        # Validar datos
        if not nombre or not codigo or not precio or not stock:
            messages.error(
                request,
                "Por favor, complete todos los campos obligatorios.",
            )
            return redirect("productos:crear")

        # Verificar que el código sea único
        if Producto.objects.filter(codigo=codigo).exists():
            messages.error(
                request,
                "El código ya existe. Por favor, use un código único.",
            )
            return redirect("productos:crear")

        try:
            precio = float(precio)
            stock = int(stock)

            # Crear el producto
            producto = Producto(
                nombre=nombre,
                codigo=codigo,
                precio=precio,
                stock=stock,
                descripcion=descripcion,
                imagen=imagen,
            )

            # Asignar categoría si se proporciona
            if categoria_id and categoria_id.isdigit():
                try:
                    categoria = Categoria.objects.get(id=categoria_id)
                    producto.categoria = categoria
                except Categoria.DoesNotExist:
                    pass

            producto.save()
            messages.success(
                request,
                f"El producto {nombre} ha sido creado exitosamente.",
            )
            return redirect("productos:detalle", producto_id=producto.id)

        except (ValueError, TypeError):
            messages.error(
                request,
                "Por favor, ingrese valores válidos para precio y stock.",
            )
            return redirect("productos:crear")

    # Si es GET, mostrar el formulario
    categorias = Categoria.objects.all()
    return render(request, "productos:crear_producto.html", {
        "categorias": categorias,
    })


@login_required
def editar_producto(request: HttpRequest, producto_id: int) -> HttpResponse:
    """Editar un producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.POST.get("nombre")
        codigo = request.POST.get("codigo")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        descripcion = request.POST.get("descripcion")
        categoria_id = request.POST.get("categoria")
        imagen = request.FILES.get("imagen")

        # Validar datos
        if not nombre or not codigo or not precio or not stock:
            messages.error(
                request,
                "Por favor, complete todos los campos obligatorios.",
            )
            return redirect("productos:editar", producto_id=producto.id)

        # Verificar que el código sea único (excepto para este producto)
        if Producto.objects.filter(codigo=codigo).exclude(id=producto_id).exists():
            messages.error(
                request,
                "El código ya existe en otro producto. Por favor, use un código único.",
            )
            return redirect("productos:editar", producto_id=producto.id)

        try:
            precio = float(precio)
            stock = int(stock)

            # Actualizar el producto
            producto.nombre = nombre
            producto.codigo = codigo
            producto.precio = precio
            producto.stock = stock
            producto.descripcion = descripcion

            # Actualizar imagen solo si se proporciona una nueva
            if imagen:
                producto.imagen = imagen

            # Actualizar categoría
            if categoria_id and categoria_id.isdigit():
                try:
                    categoria = Categoria.objects.get(id=categoria_id)
                    producto.categoria = categoria
                except Categoria.DoesNotExist:
                    producto.categoria = None
            else:
                producto.categoria = None

            producto.save()
            messages.success(
                request,
                f"El producto {nombre} ha sido actualizado exitosamente.",
            )
            return redirect("productos:detalle", producto_id=producto.id)

        except (ValueError, TypeError):
            messages.error(
                request,
                "Por favor, ingrese valores válidos para precio y stock.",
            )
            return redirect("productos:editar", producto_id=producto.id)

    # Si es GET, mostrar el formulario con los datos del producto
    categorias = Categoria.objects.all()
    return render(request, "productos/editar_producto.html", {
        "producto": producto,
        "categorias": categorias,
    })


@login_required
def eliminar_producto(request: HttpRequest, producto_id: int) -> HttpResponse:
    """Eliminar un producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(
            request,
            f"El producto {nombre} ha sido eliminado exitosamente.",
        )
        return redirect("productos:lista")

    return render(request, "productos/eliminar_producto.html", {
        "producto": producto,
    })
