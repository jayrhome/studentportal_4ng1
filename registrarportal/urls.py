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
    ]))
]
