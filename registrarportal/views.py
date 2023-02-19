from django.shortcuts import render
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateView, RedirectView, View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView, DeletionMixin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Count, Q, Case, When, Value, F
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from ratelimit.decorators import ratelimit
from adminportal.models import *
from datetime import date, datetime
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import IntegrityError
from . models import *
from studentportal.models import documentRequest
from . forms import *
from formtools.wizard.views import SessionWizardView
from adminportal.models import curriculum, schoolSections, firstSemSchedule, secondSemSchedule


User = get_user_model()


def validate_latestSchoolYear(sy):
    # Return true if school year is ongoing/latest
    try:
        return date.today() <= sy.until
    except Exception as e:
        print(e)
        return False


def registrar_only(user):
    return user.is_registrar


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class registrarDashboard(TemplateView):
    template_name = "registrarportal/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dashboard"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class getList_documentRequest(ListView, DeletionMixin):
    allow_empty = True
    context_object_name = "listOfDocumentRequests"
    http_method_names = ["get", "post"]
    paginate_by = 35
    template_name = "registrarPortal/documentRequests/listOfDocumentRequests.html"
    success_url = "/Registrar/RequestDocuments/"

    def delete(self, request, *args, **kwargs):
        try:
            self.cancel_this_request.is_cancelledByRegistrar = True
            self.cancel_this_request.save()
        except Exception as e:
            pass
        return HttpResponseRedirect(self.success_url)

    def get_queryset(self):
        return documentRequest.registrarObjects.values("id", "document__documentName", "request_by__display_name", "scheduled_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Document Requests"
        return context

    def dispatch(self, request, *args, **kwargs):
        if ("pk" in request.POST) and request.method == "POST":
            self.cancel_this_request = documentRequest.registrarObjects.filter(
                id=int(request.POST["pk"])).first()
        return super().dispatch(request, *args, **kwargs)


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class view_schoolYears(ListView):
    allow_empty = True
    context_object_name = "listOfSchoolYear"
    http_method_names = ["get"]
    paginate_by = 1
    template_name = "registrarPortal/schoolyear/listOfSchoolYear.html"

    def get_queryset(self):
        return schoolYear.objects.annotate(
            can_update=Case(When(until__gte=date.today(),
                            then=Value(True)), default=Value(False)),
            male_population=Case(
                When(pk__in=[3, 4], then=Value(100)), default=Value(50)),
            female_population=Case(
                When(pk__in=[3, 4], then=Value(100)), default=Value(50)),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "School Years"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class add_schoolYear(SessionWizardView):
    templates = {
        "add_schoolyear_form": "registrarportal/schoolyear/addSchoolYear.html",
        "ea_setup_form": "registrarportal/schoolyear/admissionScheduling.html",
    }

    form_list = [
        ("add_schoolyear_form", add_schoolyear_form),
        ("ea_setup_form", ea_setup_form),
    ]

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        try:
            sy = self.get_cleaned_data_for_step("add_schoolyear_form")
            ea = self.get_cleaned_data_for_step("ea_setup_form")

            return HttpResponseRedirect(reverse("registrarportal:addSchoolYear"))
        except Exception as e:
            return HttpResponseRedirect(reverse("registrarportal:addSchoolYear"))

    def render_goto_step(self, goto_step, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(
                self.steps.current, self.process_step(form))
            self.storage.set_step_files(
                self.steps.current, self.process_step_files(form))
        return super().render_goto_step(goto_step, **kwargs)

    def form_valid(self, form):
        try:
            # start_on = form.cleaned_data["start_on"]
            # until = form.cleaned_data["until"]

            # if start_on < until:
            #     self.new_sy = schoolYear.objects.create(
            #         start_on=start_on, until=until)
            #     messages.success(
            #         self.request, f"SY: {self.new_sy.display_sy()} is created.")
            #     return super().form_valid(form)
            # else:
            #     messages.warning(self.request, "Invalid Period. Try again.")
            #     return self.form_invalid(form)

            pass

        except Exception as e:
            pass

    def dispatch(self, request, *args, **kwargs):
        self.get_sy = schoolYear.objects.first()
        if ((self.get_sy and not validate_latestSchoolYear(self.get_sy)) or not self.get_sy) and curriculum.objects.all() and schoolSections.latestSections.all() and not self.return_sectionCount():
            return super().dispatch(request, *args, **kwargs)
        else:
            if self.get_sy and curriculum.objects.all() and schoolSections.latestSections.all() and not self.return_sectionCount():
                messages.warning(
                    self.request, "Current school year is still ongoing.")
                messages.warning(self.request, self.return_sectionCount())
            else:
                messages.warning(
                    request, "Must have a curriculum, sections, and all sections must have schedules on all subjects.")
            return HttpResponseRedirect(reverse("registrarportal:schoolyear"))

    def return_sectionCount(self):
        return schoolSections.latestSections.alias(count1Subjects=Count("first_sem_subjects"), count2Subjects=Count("second_sem_subjects"), sem1Scheds=Count("firstSemSched", filter=Q(firstSemSched__time_in__isnull=False, firstSemSched__time_out__isnull=False)), sem2Scheds=Count("secondSemSched", filter=Q(secondSemSched__time_in__isnull=False, secondSemSched__time_out__isnull=False))).exclude(Q(count1Subjects=F('sem1Scheds')), Q(count2Subjects=F('sem2Scheds'))).count()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add School Year"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class update_schoolYear(FormView):
    form_class = add_schoolyear_form
    http_method_names = ["get", "post"]
    template_name = "registrarportal/schoolyear/updateSchoolYear.html"
    success_url = "/Registrar/schoolyear/"

    def form_valid(self, form):
        if form.has_changed():
            try:
                self.sy.refresh_from_db()
                start_on = form.cleaned_data["start_on"]
                until = form.cleaned_data["until"]

                if "start_on" in form.changed_data and self.sy.start_on <= date.today():
                    messages.warning(
                        self.request, f"SY {self.sy.display_sy()} has already started. It's start date can no longer be edited.")
                    return self.form_invalid(form)

                elif ("start_on" in form.changed_data and self.sy.start_on > date.today()) or ("start_on" not in form.changed_data):
                    if start_on < until:
                        self.update_sy(form.changed_data, form)
                        messages.success(
                            self.request, f"SY {self.sy.display_sy()} is updated successfully.")
                        return super().form_valid(form)
                    messages.warning(self.request, "Invalid dates. Try again.")
                    return self.form_invalid(form)

                else:
                    return super().form_valid(form)

            except Exception as e:
                return self.form_invalid(form)
        return super().form_valid(form)

    def update_sy(self, fields, form):
        for field in fields:
            setattr(self.sy, field, form.cleaned_data[field])
        self.sy.save()
        self.sy.refresh_from_db()

    def get_initial(self):
        initial = super().get_initial()
        initial["start_on"] = self.sy.start_on
        initial["until"] = self.sy.until
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update School Year"
        context["sy"] = self.sy.display_sy()
        return context

    def dispatch(self, request, *args, **kwargs):
        self.sy = schoolYear.objects.filter(id=int(self.kwargs["pk"])).first()
        if self.sy and validate_latestSchoolYear(self.sy):
            return super().dispatch(request, *args, **kwargs)
        messages.warning(
            request, "Invalid Primary Key or object can no longer be edited.")
        return HttpResponseRedirect(reverse("registrarportal:schoolyear"))
