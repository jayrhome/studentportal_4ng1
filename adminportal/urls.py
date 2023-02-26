from django.urls import path, include, re_path
from .views import *


app_name = "adminportal"

urlpatterns = [
    path("", index.as_view(), name="index"),

    path("Courses/", include([
        path("", shs_courses.as_view(), name="view_courses"),
        path("add_track/", add_courseTrack.as_view(), name="add_track"),
        path("Track_details/<track_id>/",
             edit_courseTrack.as_view(), name="edit_track"),
        path("Delete_track/<pk>/", delete_courseTrack.as_view(), name="delete_track"),
        path("Add_strand/<track_id>/",
             add_trackStrand.as_view(), name="add_strand"),
        path("Edit_strand/<strand_id>/",
             update_trackStrand.as_view(), name="edit_strand"),
        path("Delete_strand/<pk>/",
             delete_trackStrand.as_view(), name="delete_strand"),
    ])),

    #     path("Admission_and_enrollment/", include([
    #         path("", admission_and_enrollment.as_view(),
    #              name="admission_and_enrollment"),
    #         path("Setup/", open_enrollment_admission.as_view(),
    #              name="admission_enrollment_setup"),
    #         path("Update_details/<uid>/", update_enrollment.as_view(),
    #              name="setup_details_update"),
    #         path("Extend_details/<uid>/", extend_enrollment.as_view(),
    #              name="extend_enrollment"),
    #         path("Postpone_enrollment/<uid>/",
    #              postpone_enrollment.as_view(), name="postpone_enrollment"),

    #         re_path(r"Admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                 admission.as_view(), name="admission"),
    #         re_path(r"Admitted_students/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                 admitted_students.as_view(), name="admitted_students"),
    #         path("Details/<pk>/", adm_details.as_view(), name="details"),
    #         re_path(r"For_review/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                 review_admissionList.as_view(), name="forReviewAdmission"),
    #         re_path(r"Denied_admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                 denied_admissionList.as_view(), name="denied_admissions"),
    #         re_path(r"Hold_admission/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                 hold_admissionList.as_view(), name="hold_admissions"),

    #         path("Enrollment/", include([
    #             re_path(r"(?:(?P<dts>[a-zA-Z\d\s]+)/)?$", pending_enrollment_list.as_view(),
    #                     name="pending_enrollment"),
    #             re_path(r"Enrolled_students/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                     enrolled_students.as_view(), name="enrolled_students"),
    #             re_path(r"For_review_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                     for_review_enrollmentList.as_view(), name="ForReviewEnrollmentLists"),
    #             re_path(r"Denied_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                     denied_enrollment_list.as_view(), name="denied_enrollment_lists"),
    #             re_path(r"Hold_enrollments/(?:(?P<dts>[a-zA-Z\d\s]+)/)?$",
    #                     hold_enrollment_lists.as_view(), name="hold_enrollment_lists"),
    #             path("Enrollment_details/<pk>", enrollment_details.as_view(),
    #                  name="enrollment_details"),
    #         ])),
    #     ])),

    path("schoolDocuments/", include([
        path("", view_schoolDocuments_canRequest.as_view(), name="schoolDocuments"),
        re_path(r"AddOrEdit/(?:(?P<docuId>[0-9]+)/)?$",
                addEditDocument.as_view(), name="addEditDocument"),
        path("hideDocument/<pk>/", hideDocument.as_view(), name="hideDocument"),
    ])),

    path("school_events/", include([
        path("", get_ongoingSchoolEvents.as_view(),
             name="get_ongoingSchoolEvents"),
        path("Add/", add_schoolEvent.as_view(), name="add_schoolEvent"),
        path("Update/<pk>/", edit_schoolEvent.as_view(), name="edit_schoolEvent"),
    ])),

    re_path(r"subjects/(?:(?P<key>[a-zA-ZñÑ\d\s]+)/)?$",
            get_subjects.as_view(), name="getSubjects"),

    path("Subject/", include([
        path("Add/", add_subjects.as_view(), name="addSubjects"),
        path("Update/<pk>", update_subjects.as_view(), name="updateSubjects"),
    ])),

    path("Curriculums/", include([
        path("", view_curriculum.as_view(), name="view_curriculum"),
        path("Add/", add_curriculum.as_view(), name="add_curriculum"),
        path("Update/<pk>", update_curriculum.as_view(), name="update_curriculum"),
    ])),

    path("Sections/", include([
        re_path(r"(?:(?P<year>[0-9]+)/)?$",
                get_sections.as_view(), name="get_sections"),
        path("Generate/", make_section.as_view(), name="new_section"),
        path("Scheduling/", generate_classSchedule.as_view(),
             name="generate_classSchedule"),
    ])),

]
