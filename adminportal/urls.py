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

        re_path(r"Admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                admission.as_view(), name="admission"),
        re_path(r"Admitted_students/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                admitted_students.as_view(), name="admitted_students"),
        path("Details/<pk>/", adm_details.as_view(), name="details"),
        re_path(r"For_review/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                review_admissionList.as_view(), name="forReviewAdmission"),
        re_path(r"Denied_admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                denied_admissionList.as_view(), name="denied_admissions"),
        re_path(r"Hold_admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                hold_admissionList.as_view(), name="hold_admissions"),

        path("Enrollment/", include([
            re_path(r"(?:(?P<dts>[a-zA-Z\d\s]+)/)?$", pending_enrollment_list.as_view(),
                    name="pending_enrollment"),
            re_path(r"Enrolled_students/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                    enrolled_students.as_view(), name="enrolled_students"),
            re_path(r"For_review_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                    for_review_enrollmentList.as_view(), name="ForReviewEnrollmentLists"),
            re_path(r"Denied_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                    denied_enrollment_list.as_view(), name="denied_enrollment_lists"),
            re_path(r"Hold_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
                    hold_enrollment_lists.as_view(), name="hold_enrollment_lists"),
            path("Enrollment_details/<pk>", enrollment_details.as_view(),
                 name="enrollment_details"),
        ])),
    ])),

    path("school_events/", include([
        path("", upcoming_school_events.as_view(), name="upcomingschoolevents"),
        path("ongoing_events/", ongoing_school_events.as_view(),
             name="ongoingschoolevents"),
        path("previous_events/", previous_school_events.as_view(),
             name="previousschoolevents"),
        path("add_events/", add_event.as_view(), name="addschoolevents"),

    ])),

    path("students/", include([
        path("", valid_student_accounts.as_view(), name="validstudentaccounts"),
        path("invalid_accounts/", invalid_student_accounts.as_view(),
             name="invalidstudentaccounts"),
        path("honor_students/", honor_students.as_view(), name="honorstudents"),
    ])),

    path("subjects/", include([
        path("", get_subject_lists.as_view(), name="getsubjects"),
        path("add_subject/", add_subject.as_view(), name="addsubjects"),
        path("update_subject/", update_subject.as_view(), name="updatesubject"),
        path("assign_subject_teachers/",
             assign_subject_teachers.as_view(), name="assignsubjectteachers"),
    ])),

    path("sections/", include([
        path("", get_section_lists.as_view(), name="getsectionlist"),
        path("add_section/", add_section.as_view(), name="addsection"),
    ])),

    path("teachers/", include([
        path("", school_teachers.as_view(), name="schoolteachers"),
    ])),

    path("grade_computation/", include([
        path("", grade_formula.as_view(), name="gradeformula"),
    ])),

    path("schoolDocuments/", include([
        path("", view_schoolDocuments_canRequest.as_view(), name="schoolDocuments"),
        re_path(r"AddOrEdit/(?:(?P<docuId>[0-9]+)/)?$",
                addEditDocument.as_view(), name="addEditDocument"),
        path("hideDocument/<pk>/", hideDocument.as_view(), name="hideDocument"),
    ])),

]
