from django.urls import path, include
from . views import *
from . import views

app_name = "registrarportal"

urlpatterns = [
    path("", registrarDashboard.as_view(), name="dashboard"),
]
