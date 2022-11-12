from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, FormMixin
from django.views.generic.detail import DetailView
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
    # View courses
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
            if shs_track.objects.filter(track_name=name, is_deleted=False).exists():
                messages.warning(self.request, "%s already exist." % name)
                return self.form_invalid(form)
            elif shs_track.objects.filter(track_name=name, is_deleted=True).exists():
                shs_track.objects.filter(track_name=name, is_deleted=True).update(
                    track_name=name,
                    definition=details,
                    is_deleted=False
                )
                messages.success(
                    self.request, "%s is added successfully." % name)
                return super().form_valid(form)
            else:
                shs_track.objects.create(track_name=name, definition=details)
                messages.success(
                    self.request, "%s is added successfully." % name)
                return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request, "%s already exist. Duplicate is not allowed." % name)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Course"
        return context


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class edit_track(FormView):
    template_name = "adminportal/edit_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

    def get_initial(self):
        initial = super().get_initial()
        qs = shs_track.objects.get(id=self.kwargs["track_id"])
        initial["name"] = qs.track_name
        initial["details"] = qs.definition
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Track"
        return context

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        details = form.cleaned_data["details"]

        try:
            if name and details:
                obj = shs_track.objects.filter(
                    id=self.kwargs["track_id"]).first()
                if obj:
                    if obj.is_deleted == True:
                        messages.warning(
                            self.request, "%s no longer exist." % name)
                        return super().form_valid(form)
                    else:
                        shs_track.objects.filter(id=self.kwargs["track_id"]).update(
                            track_name=name,
                            definition=details
                        )
                        messages.success(
                            self.request, "%s is updated successfully." % name)
                        return super().form_valid(form)
                else:
                    messages.warning(
                        self.request, "%s no longer exist." % name)
                    return super().form_valid(form)
            else:
                messages.warning(self.request, "Fill all fields.")
                return self.form_invalid(form)
        except IntegrityError:
            messages.error(
                self.request, "%s already exist. Duplicate is not allowed." % name)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, e)
            return self.form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if shs_track.objects.filter(id=self.kwargs["track_id"], is_deleted=True).exists():
            messages.warning(
                request, "Course Track with id no. %s no longer exist." % self.kwargs["track_id"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        elif not shs_track.objects.filter(id=self.kwargs["track_id"]).exists():
            messages.warning(
                request, "Course Track with id no. %s does not exist." % self.kwargs["track_id"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        else:
            return super().dispatch(request, *args, **kwargs)


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class delete_track(TemplateView):
    template_name = "adminportal/delete_track.html"

    def post(self, request, *args, **kwargs):
        obj = shs_track.objects.filter(id=self.kwargs["pk"]).update(
            is_deleted=True
        )
        objj = shs_track.objects.get(id=self.kwargs["pk"])
        messages.success(request, "%s is deleted successfully." %
                         objj.track_name)
        return HttpResponseRedirect(reverse("adminportal:view_courses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["obj"] = shs_track.objects.filter(id=self.kwargs["pk"]).first()
        return context

    def dispatch(self, request, *args, **kwargs):
        if shs_track.objects.filter(id=self.kwargs["pk"], is_deleted=True).exists():
            messages.warning(
                request, "Course Track with id no. %s no longer exist." % self.kwargs["pk"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        elif not shs_track.objects.filter(id=self.kwargs["pk"]).exists():
            messages.warning(
                request, "Course Track with id no. %s does not exist." % self.kwargs["pk"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        else:
            return super().dispatch(request, *args, **kwargs)
