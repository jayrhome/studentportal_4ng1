from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from . forms import add_shs_track
from . models import *
from django.db import IntegrityError
from django.contrib import messages
from django.db.models import Q, FilteredRelation, Prefetch


def superuser_only(user):
    return user.is_superuser


def add_school_year(start_year, year):
    try:
        return start_year.replace(year=start_year.year + year)
    except ValueError:
        return start_year.replace(year=start_year.year + year, day=28)


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class index(TemplateView):
    template_name = "adminportal/index.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class shs_courses(TemplateView):
    template_name = "adminportal/courses.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Courses"
        context["courses"] = shs_track.objects.filter(is_deleted=False).prefetch_related(Prefetch(
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False), to_attr="strands"))

        return context


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class add_shs_track_cbv(FormView):
    template_name = "adminportal/create_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        details = form.cleaned_data["details"]

        try:
            shs_track.objects.create(track_name=name, definition=details)
            messages.success(self.request, "%s is added successfully." % name)
            return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request, "%s already exist. Duplicate is not allowed." % name)
            return self.form_invalid(form)
        except:
            messages.error(
                self.request, "Your data did not save. Try again.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Course"
        return context
