from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "usersPortal"

urlpatterns = [
    path("", create_useraccount.as_view(), name="create_useraccount"),
    path("Activate_account/<uidb64>/<token>",
         views.activate_account, name="activate_account"),
]
