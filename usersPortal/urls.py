from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "usersPortal"

urlpatterns = [
    path("", include([
        path("", create_useraccount.as_view(), name="create_useraccount"),
        path("create_adminAccount/", create_adminAccount.as_view(),
             name="create_adminAccount"),
        path("create_registrarAccount/", create_registrarAccount.as_view(),
             name="create_registrarAccount"),
    ])),

    path("Activate_account/<uidb64>/<token>",
         views.activate_account, name="activate_account"),
    path("login/", login.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("Request_authentication/", request_newAccountActivationToken.as_view(),
         name="requestAuthentication"),
    path("ForgotPassword/", forgotPassword.as_view(), name="forgotpassword"),
    path("PasswordReset/<uidb64>/<token>",
         passwordReset.as_view(), name="password_reset"),

    path("Profile/", include([
        path("", userAccountProfile.as_view(), name="account_profile"),
        path("Edit/", updateAccountProfile.as_view(),
             name="updateAccountProfile"),
        path("Change_password/", userChangePassword.as_view(),
             name="changepassword"),
        path("ResetPassword/", authenticatedUser_resetPassword.as_view(),
             name="resetpassword"),
    ])),
]
