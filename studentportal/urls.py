from django.urls import path
from . views import *
from . import views

app_name = "studentportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
    path("login/", login.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("create/", create_useraccount.as_view(), name="createaccount"),
    path("Activate_account/<uidb64>/<token>", views.activate, name="activate"),
]
