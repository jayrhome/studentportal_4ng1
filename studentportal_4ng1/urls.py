from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("studentportal.urls")),
    path('School_admin/', include("adminportal.urls")),
    path('Registrar/', include("registrarportal.urls")),
    path('users/', include("usersPortal.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def page_not_found(request, exception=None):
    return render(request, "error_HTMLs/404.html")


handler404 = page_not_found
