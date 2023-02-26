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

            if ea["start_date"] >= ea["end_date"]:
                messages.warning(
                    self.request, "Invalid dates to start the admission.")
                return HttpResponseRedirect(reverse("registrarportal:addSchoolYear"))
            self.create_schoolyear(sy)
            self.start_admission(ea)
            messages.success(
                self.request, f"SY: {self.new_sy.display_sy()} is created.")
            return HttpResponseRedirect(reverse("registrarportal:schoolyear"))
        except Exception as e:
            return HttpResponseRedirect(reverse("registrarportal:addSchoolYear"))

    def render_next_step(self, form, **kwargs):
        get_data = self.get_cleaned_data_for_step(self.storage.current_step)
        if self.storage.current_step == "add_schoolyear_form" and get_data["start_on"] >= get_data["until"]:
            messages.warning(
                self.request, "Invalid dates for creating a school year.")
            return self.render_goto_step(self.storage.current_step, **kwargs)
        else:
            next_step = self.steps.next
            new_form = self.get_form(
                next_step,
                data=self.storage.get_step_data(next_step),
                files=self.storage.get_step_files(next_step),
            )
            # change the stored current step
            self.storage.current_step = next_step
            return self.render(new_form, **kwargs)

    def render_goto_step(self, goto_step, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(
                self.steps.current, self.process_step(form))
            self.storage.set_step_files(
                self.steps.current, self.process_step_files(form))
        return super().render_goto_step(goto_step, **kwargs)

    def create_schoolyear(self, form):
        try:
            self.new_sy = schoolYear.objects.create(
                start_on=form["start_on"], until=form["until"])
        except Exception as e:
            pass

    def start_admission(self, form):
        try:
            enrollment_admission_setup.objects.create(
                ea_setup_sy=self.new_sy, start_date=form["start_date"], end_date=form["end_date"], students_perBatch=form["students_perBatch"])
        except Exception as e:
            pass

    def dispatch(self, request, *args, **kwargs):
        self.get_sy = schoolYear.objects.first()
        if ((self.get_sy and not validate_latestSchoolYear(self.get_sy)) or not self.get_sy) and curriculum.objects.all():
            return super().dispatch(request, *args, **kwargs)
        else:
            if validate_latestSchoolYear(self.get_sy):
                messages.warning(
                    self.request, "Current school year is still ongoing.")
            else:
                messages.warning(
                    request, "Must have a curriculum to start the admission.")
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


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class get_admissions(ListView, DeletionMixin):
    allow_empty = True
    context_object_name = "batches"
    paginate_by = 1
    template_name = "registrarportal/admission/getRequests.html"
    http_method_names = ["get", "post"]
    success_url = "/Registrar/Admission/"

    def delete(self, request, *args, **kwargs):
        if "decPk" in request.POST:
            self.denied_this_admission.is_denied = True
            self.denied_this_admission.save()

        if "batchId" in request.POST:
            if schoolSections.latestSections.filter(sy=self.get_batch.sy, yearLevel="11").exists():
                studAdms = student_admission_details.objects.filter(
                    admission_batch_member__id=self.get_batch.id, is_accepted=False).exclude(is_denied=True).values_list('id', flat=True)
                student_admission_details.admit_this_students(studAdms)
            messages.warning(
                request, "School must have new sections for grade 11 admission.")

        return HttpResponseRedirect(self.success_url + f"?page={request.POST.get('page')}")

    def get_queryset(self):
        try:
            qs = admission_batch.new_batches.alias(count_applicants=Count("members", filter=Q(members__is_accepted=False, members__is_denied=False))).filter(count_applicants__gte=1).prefetch_related(Prefetch("members", queryset=student_admission_details.objects.filter(is_accepted=False, is_denied=False).prefetch_related(Prefetch(
                "softCopy_admissionRequirements_phBorn", queryset=ph_born.objects.all(), to_attr="phborn"), Prefetch("softCopy_admissionRequirements_foreigner", queryset=foreign_citizen_documents.objects.all(), to_attr="foreign"), Prefetch("softCopy_admissionRequirements_dualCitizen", queryset=dual_citizen_documents.objects.all(), to_attr="dualcitizen")), to_attr="applicants"))
        except Exception as e:
            qs = admission_batch.new_batches.none()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Admission"
        return context

    def dispatch(self, request, *args, **kwargs):
        if ("decPk" in request.POST) and request.method == "POST":
            self.denied_this_admission = student_admission_details.objects.filter(
                id=int(request.POST["decPk"])).first()

        if ("batchId" in request.POST) and request.method == "POST":
            self.get_batch = admission_batch.new_batches.filter(
                id=int(request.POST["batchId"])).first()
        return super().dispatch(request, *args, **kwargs)
