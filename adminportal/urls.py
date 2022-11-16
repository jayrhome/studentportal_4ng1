from django.urls import path, include
from .views import *


app_name = "adminportal"

urlpatterns = [
    path("", index.as_view(), name="index"),

    path("Courses/", include([
        path("", shs_courses.as_view(), name="view_courses"),
        path("add_track/", add_shs_track_cbv.as_view(), name="add_track"),
        path("Track_details/<track_id>/",
             edit_track.as_view(), name="edit_track"),
        path("Delete_track/<pk>/", delete_track.as_view(), name="delete_track"),
        path("Add_strand/<track_id>/",
             add_strand.as_view(), name="add_strand"),
        path("Edit_strand/<strand_id>/",
             edit_strand.as_view(), name="edit_strand"),
        path("Delete_strand/<pk>/", delete_strand.as_view(), name="delete_strand"),
    ])),

    path("Admission_and_enrollment/", include([
        path("", admission_and_enrollment.as_view(),
             name="admission_and_enrollment"),
        path("Setup/", open_enrollment_admission.as_view(),
             name="admission_enrollment_setup"),
    ])),

]
