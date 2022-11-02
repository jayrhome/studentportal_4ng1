from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("studentportal.urls")),
    path('School_admin/', include("adminportal.urls")),
    path('Teachers/', include("teachersportal.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
