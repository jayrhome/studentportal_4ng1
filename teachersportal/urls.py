from django.urls import path, include
from .views import *


app_name = "teachersportal"

urlpatterns = [
    path("", index.as_view(), name="index"),
    path("class_list/", class_list.as_view(), name="classlist"),
    path("class_record/", class_record.as_view(), name="classrecord"),
    path("class_assessments/", class_assessments.as_view(), name="classassessments"),
    path("class_learningmaterials/", class_learningmaterials.as_view(),
         name="class_learningmaterials"),
    path("class_chatbox/", class_chatbox.as_view(), name="class_chatbox"),
]
