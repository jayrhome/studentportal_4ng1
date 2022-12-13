from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse


def teachers_only(user):
    return user.is_teacher


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class index(TemplateView):
    template_name = "teachersportal/index.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class class_list(TemplateView):
    template_name = "teachersportal/classlist.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class class_record(TemplateView):
    template_name = "teachersportal/classrecord.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class class_assessments(TemplateView):
    template_name = "teachersportal/class_assessments.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class class_learningmaterials(TemplateView):
    template_name = "teachersportal/learning_materials.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(teachers_only, login_url="studentportal:index")], name="dispatch")
class class_chatbox(TemplateView):
    template_name = "teachersportal/groupchatbox.html"
