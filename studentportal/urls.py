from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "studentportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
    path("login/", login.as_view(), name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("Password_reset/", password_reset.as_view(), name="password_reset"),
    path("Password_reset_form/<uidb64>/<token>",
         password_reset_form.as_view(), name="password_reset_form"),

    path("Admission/", include([
        path("", admission_application.as_view(), name="admission_application"),
        path("Admission_details/", submitted_admission_details.as_view(),
             name="admission_details")
    ])),

    path("Enrollment/", include([
        path("", enrollment_application.as_view(),
             name="enrollment_application"),
        re_path(r"Enrollment_details/(?:(?P<pk>[0-9]+)/)?$",
                submitted_enrollment_details.as_view(), name="enrollment_details"),
    ])),
]
