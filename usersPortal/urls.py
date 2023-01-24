from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "usersPortal"

urlpatterns = [
    path("", create_useraccount.as_view(), name="create_useraccount"),
]
