from django.urls import path
from .views import index


app_name = "teachersportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
]
