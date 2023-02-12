from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "studentportal"

urlpatterns = [
    path("", index.as_view(), name="index"),

    #     path("Admission/", include([
    #         path("", admission_application.as_view(), name="admission_application"),
    #         path("Admission_details/", submitted_admission_details.as_view(),
    #              name="admission_details")
    #     ])),

    #     path("Enrollment/", include([
    #         path("", enrollment_application.as_view(),
    #              name="enrollment_application"),
    #         re_path(r"Enrollment_details/(?:(?P<pk>[0-9]+)/)?$",
    #                 submitted_enrollment_details.as_view(), name="enrollment_details"),
    #     ])),

    path("DocumentRequests/", include([
        path("", view_myDocumentRequest.as_view(),
             name="view_myDocumentRequest"),
        path("requestdocument/", create_documentRequest.as_view(),
             name="create_documentRequest"),
        path("resched/<pk>", reschedDocumentRequest.as_view(),
             name="reschedDocumentRequest"),
    ])),
]
