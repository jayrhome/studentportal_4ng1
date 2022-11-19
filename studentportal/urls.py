from django.urls import path, include
from . views import *
from . import views

app_name = "studentportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
    path("login/", login.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("create/", create_useraccount.as_view(), name="createaccount"),
    path("Activate_account/<uidb64>/<token>",
         views.activate_account, name="activate_account"),
    path("Password_reset/", password_reset.as_view(), name="password_reset"),
    path("Password_reset_form/<uidb64>/<token>",
         password_reset_form.as_view(), name="password_reset_form"),

    path("Application/", include([
        path("", admission_application.as_view(), name="application"),
    ]))
]
