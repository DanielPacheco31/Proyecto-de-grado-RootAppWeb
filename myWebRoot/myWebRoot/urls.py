"""URL configuration for myWebRoot project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("productos/", include("productos.urls")),
    path("carrito/", include("carrito.urls")),
    path("pagos/", include("pagos.urls")),
    path("facturas/", include("facturas.urls")),
    path("scanner/", include("scanner.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
