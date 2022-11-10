from django.urls import path, include
from .views import *


app_name = "adminportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
    path("Courses/", include([
        path("", shs_courses.as_view(), name="view_courses"),
        path("add_track/", add_shs_track_cbv.as_view(), name="add_track"),
    ]))

]
