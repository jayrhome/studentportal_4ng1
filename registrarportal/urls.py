from django.urls import path, include, re_path
from . views import *
from . import views

app_name = "registrarportal"

urlpatterns = [
    path("", registrarDashboard.as_view(), name="dashboard"),
    path("RequestDocuments/", getList_documentRequest.as_view(),
         name="requestedDocuments"),

    path("schoolyear/", include([
        path("", view_schoolYears.as_view(), name="schoolyear"),
        path("Add/", add_schoolYear.as_view(), name="addSchoolYear"),
        path("Update/<pk>/", update_schoolYear.as_view(), name="updateSchoolYear"),
    ])),

    path("Admission/", include([
        path("", get_admissions.as_view(), name="view_admissions"),
        path("enrollment_generate/", enrollment_invitation_oldStudents.as_view(),
             name="enrollment_invitation_oldStudents"),
        path("Update_schedule/", update_admission_schedule.as_view(),
             name="update_admission_schedule"),
        re_path(r"admitted_students/(?:(?P<key>[a-zA-Z\d\s]+)/)?$",
                get_admitted_students.as_view(), name="get_admitted_students"),
    ])),

    path("Enrollment/", include([
        re_path(r"Enrolled_students/(?:(?P<key>[a-zA-Z\d\s]+)/)?$",
                get_enrolled_students.as_view(), name="get_enrolled_students"),
    ])),
]
