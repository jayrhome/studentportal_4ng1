from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse


@method_decorator(login_required(login_url="studentportal:login"), name="dispatch")
class index(TemplateView):
    template_name = "adminportal/index.html"
