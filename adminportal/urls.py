from django.urls import path, include, re_path
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
        path("Delete_strand/<pk>/",
             delete_strand.as_view(), name="delete_strand"),
    ])),

    path("Admission_and_enrollment/", include([
        path("", admission_and_enrollment.as_view(),
             name="admission_and_enrollment"),
        path("Setup/", open_enrollment_admission.as_view(),
             name="admission_enrollment_setup"),
        path("Update_details/<uid>/", update_enrollment.as_view(),
             name="setup_details_update"),
        path("Extend_details/<uid>/", extend_enrollment.as_view(),
             name="extend_enrollment"),
        path("Postpone_enrollment/<uid>/",
             postpone_enrollment.as_view(), name="postpone_enrollment"),

        re_path(r"Admission/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                admission.as_view(), name="admission"),
        re_path(r"Admitted_students/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                admitted_students.as_view(), name="admitted_students"),
        path("Details/<pk>/", adm_details.as_view(), name="details"),
        re_path(r"For_review/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                review_admissionList.as_view(), name="forReviewAdmission"),
        re_path(r"Denied_admission/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                denied_admissionList.as_view(), name="denied_admissions"),
        re_path(r"Hold_admission/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                hold_admissionList.as_view(), name="hold_admissions"),

        path("Enrollment/", include([
            re_path(r"(?:(?P<dts>[a-zA-Z\d]+)/)?$", pending_enrollment_list.as_view(),
                    name="pending_enrollment"),
            re_path(r"Enrolled_students/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                    enrolled_students.as_view(), name="enrolled_students"),
            re_path(r"For_review_enrollments/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                    for_review_enrollmentList.as_view(), name="ForReviewEnrollmentLists"),
            re_path(r"Denied_enrollments/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                    denied_enrollment_list.as_view(), name="denied_enrollment_lists"),
            re_path(r"Hold_enrollments/(?:(?P<dts>[a-zA-Z\d]+)/)?$",
                    hold_enrollment_lists.as_view(), name="hold_enrollment_lists"),
        ]))
    ])),


]
