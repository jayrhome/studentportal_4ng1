from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "usersPortal"

urlpatterns = [
    path("", create_useraccount.as_view(), name="create_useraccount"),
    path("Activate_account/<uidb64>/<token>",
         views.activate_account, name="activate_account"),
    path("login/", login.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("Request_authentication/", request_newAccountActivationToken.as_view(),
         name="requestAuthentication"),
    path("ForgotPassword/", forgotPassword.as_view(), name="forgotpassword"),
    path("PasswordReset/<uidb64>/<token>",
         passwordReset.as_view(), name="password_reset"),
]
