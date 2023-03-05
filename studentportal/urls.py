from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "studentportal"

urlpatterns = [
    path("", index.as_view(), name="index"),

    path("DocumentRequests/", include([
        path("", view_myDocumentRequest.as_view(),
             name="view_myDocumentRequest"),
        path("requestdocument/", create_documentRequest.as_view(),
             name="create_documentRequest"),
        path("resched/<pk>", reschedDocumentRequest.as_view(),
             name="reschedDocumentRequest"),
    ])),

    path("admission/", include([
        path("applicantType/", select_admission_type.as_view(), name="select_type"),
        re_path(r"type/(?:(?P<pk>[0-9]+)/)?$",
                admission.as_view(), name="admission"),
    ])),

    path("Enrollment/", include([
        path("apply/<uidb64>/<token>/",
             enrollment_new_admission.as_view(), name="enrollment_new_admission"),
        path("Old_students/<uidb64>/<token>/",
             enrollment_old_students.as_view(), name="oldStudents_enrollment"),
    ])),

    path("Applications/", include([
        path("", get_submitted_admission.as_view(),
             name="get_submitted_admission"),
        path("Resubmit/", resend_admission.as_view(), name="resend_admission"),
    ])),
]
