from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, FormMixin, DeletionMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, datetime, timedelta
from . forms import *
from . models import *
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import Q, FilteredRelation, Prefetch, Count, Case, When, Value, F
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from formtools.wizard.views import SessionWizardView
from string import ascii_uppercase


def superuser_only(user):
    return user.is_superuser


def add_school_year(start_year, year):
    try:
        return start_year.replace(year=start_year.year + year)
    except ValueError:
        return start_year.replace(year=start_year.year + year, day=28)


def compute_schoolyear(year):
    date_now = date.today()
    future_date = add_school_year(date_now, year)
    sy = " ".join(
        map(str, [date_now.strftime("%Y"), "-", future_date.strftime("%Y")]))
    return sy


# validate the latest school year
def validate_enrollmentSetup(request, sy):
    try:
        dt1 = date.today()
        dt2 = sy.date_created.date()
        dt3 = dt1 - dt2

        if dt3.days < 209:
            return True
        return False
    except:
        return False


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class index(TemplateView):
    template_name = "adminportal/dashboard.html"


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class shs_courses(TemplateView):
    # View courses
    template_name = "adminportal/Shs_courses/courses.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Courses"
        context["courses"] = shs_track.objects.filter(is_deleted=False).prefetch_related(Prefetch(
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False), to_attr="strands")).order_by("track_name")

        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_courseTrack(FormView):
    template_name = "adminportal/Shs_courses/create_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

    def get_success_url(self):
        if "another" in self.request.POST:
            return "/School_admin/Courses/add_track/"
        else:
            return super().get_success_url()

    def form_valid(self, form):
        try:
            name = form.cleaned_data["name"]
            details = form.cleaned_data["details"]

            if name and details:
                self.get_existingTrack = shs_track.objects.filter(
                    track_name=name).first()
                if self.get_existingTrack:
                    if not self.get_existingTrack.is_deleted:
                        messages.warning(
                            self.request, f"{name} already exist.")
                        return self.form_invalid(form)
                    else:
                        self.get_existingTrack.track_name = name
                        self.get_existingTrack.definition = details
                        self.get_existingTrack.is_deleted = False
                        self.get_existingTrack.save()
                        messages.success(
                            self.request, f"{name} is updated successfully.")
                        return super().form_valid(form)
                else:
                    shs_track.objects.create(
                        track_name=name, definition=details)
                    messages.success(
                        self.request, f"{name} is added successfully.")
                    return super().form_valid(form)
            else:
                messages.warning(self.request, "Fill all fields.")
                return self.form_invalid(form)

        except IntegrityError:
            messages.error(
                self.request, f"{name} already exist. Duplicate is not allowed.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Course Track"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class edit_courseTrack(FormView):
    template_name = "adminportal/Shs_courses/edit_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

    def get_initial(self):
        initial = super().get_initial()
        initial["name"] = self.updateCourseTrackObject.track_name
        initial["details"] = self.updateCourseTrackObject.definition
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Course Track"
        return context

    def form_valid(self, form):
        try:
            name = form.cleaned_data["name"]
            details = form.cleaned_data["details"]

            if form.has_changed():
                if name and details:
                    self.updateCourseTrackObject.refresh_from_db()
                    self.updateCourseTrackObject.track_name = name
                    self.updateCourseTrackObject.definition = details
                    self.updateCourseTrackObject.save()
                    messages.success(
                        self.request, f"{name} is updated successfully.")
                    return super().form_valid(form)
                else:
                    messages.warning(self.request, "Fill all fields.")
                    return self.form_invalid(form)
            else:
                return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request, f"{name} already exist. Duplicate is not allowed.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        self.updateCourseTrackObject = shs_track.objects.filter(
            id=int(self.kwargs["track_id"])).first()
        if self.updateCourseTrackObject:
            if not self.updateCourseTrackObject.is_deleted:
                return super().dispatch(request, *args, **kwargs)
            else:
                messages.warning(request, "Course track does not exist.")
                return HttpResponseRedirect(reverse("adminportal:view_courses"))
        else:
            messages.warning(
                request, f"Course track with id no. {self.kwargs['track_id']} does not exist.")
            return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class delete_courseTrack(TemplateView):
    template_name = "adminportal/Shs_courses/delete_track.html"

    def post(self, request, *args, **kwargs):
        try:
            self.deleteTrack.refresh_from_db()

            for strand in shs_strand.objects.filter(track=self.deleteTrack):
                strand.is_deleted = True
                strand.save()

            self.deleteTrack.is_deleted = True
            self.deleteTrack.save()
            messages.success(
                request, f"{self.deleteTrack.track_name} is deleted.")
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        except Exception as e:
            return HttpResponseRedirect(reverse("adminportal:view_courses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Remove Course Track"
        context["courseObjects"] = shs_track.objects.filter(id=self.deleteTrack.id).prefetch_related(Prefetch(
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False), to_attr="strands")).first()
        return context

    def dispatch(self, request, *args, **kwargs):
        self.deleteTrack = shs_track.objects.filter(
            id=int(self.kwargs["pk"])).first()
        if self.deleteTrack:
            if not self.deleteTrack.is_deleted:
                return super().dispatch(request, *args, **kwargs)
            messages.warning(request, "Course track does not exist.")
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        messages.warning(request, "Course track does not exist.")
        return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_trackStrand(FormView):
    success_url = "/School_admin/Courses/"
    form_class = add_strand_form
    template_name = "adminportal/Shs_courses/create_strands.html"

    def get_success_url(self):
        if "another" in self.request.POST:
            return "/School_admin/Courses/Add_strand/" + self.kwargs["track_id"]
        else:
            return super().get_success_url()

    def form_valid(self, form):
        try:
            strand_name = form.cleaned_data["strand_name"]
            strand_details = form.cleaned_data["strand_details"]

            if form.has_changed():
                if strand_name and strand_details:
                    self.getStrand = shs_strand.objects.filter(
                        strand_name=strand_name).first()
                    if self.getStrand:
                        # if strand name already exist
                        if not self.getStrand.is_deleted:
                            # if the existing strand name is not deleted
                            messages.warning(
                                self.request, f"{strand_name} already exist.")
                            return self.form_invalid(form)
                        else:
                            # if the existing strand is deleted
                            if self.getStrand.track == self.getTrack:
                                self.getStrand.strand_name = strand_name
                                self.getStrand.definition = strand_details
                                self.getStrand.is_deleted = False
                                self.getStrand.save()
                                messages.success(
                                    self.request, f"{strand_name} is added to {self.getTrack.track_name}")
                                return super().form_valid(form)
                            messages.warning(
                                self.request, f"{strand_name} is being used on other track.")
                            return self.form_invalid(form)
                    else:
                        # If strand name is unique, then, Create new strand
                        shs_strand.objects.create(
                            track=self.getTrack,
                            strand_name=strand_name,
                            definition=strand_details,
                        )
                        messages.success(
                            self.request, f"{strand_name} is added to {self.getTrack.track_name}")
                        return super().form_valid(form)

                else:
                    # if empty fields
                    messages.warning(self.request, "Fill all fields")
                    return self.form_invalid(form)
            else:
                return super().form_valid(form)
        except IntegrityError:
            messages.warning(self.request, f"{strand_name} already exist.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["track"] = self.getTrack.track_name
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Track Strand"
        return context

    def dispatch(self, request, *args, **kwargs):
        self.getTrack = shs_track.objects.filter(
            id=int(self.kwargs["track_id"])).first()
        if self.getTrack:
            self.getTrack.refresh_from_db()
            if not self.getTrack.is_deleted:
                return super().dispatch(request, *args, **kwargs)
            messages.warning(request, "Track course no longer exist.")
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        else:
            messages.warning(request, "Track course does not exist.")
            return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class update_trackStrand(FormView):
    template_name = "adminportal/Shs_courses/edit_strand.html"
    form_class = edit_strand_form
    success_url = "/School_admin/Courses/"

    def form_valid(self, form):
        try:
            strand_name = form.cleaned_data["strand_name"]
            strand_details = form.cleaned_data["strand_details"]

            if form.has_changed():
                if strand_name and strand_details:
                    self.getStrand.strand_name = strand_name
                    self.getStrand.definition = strand_details
                    self.getStrand.save()
                    messages.success(
                        self.request, f"{strand_name} is updated successfully.")
                    return super().form_valid(form)
                else:
                    messages.warning(self.request, "Fill all fields.")
                    return self.form_invalid(form)
            else:
                return super().form_valid(form)
        except IntegrityError:
            messages.warning(self.request, f"{strand_name} already exist.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["track"] = self.getStrand.track.track_name
        initial["strand_name"] = self.getStrand.strand_name
        initial["strand_details"] = self.getStrand.definition
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Track Strand"
        return context

    def dispatch(self, request, *args, **kwargs):
        self.getStrand = shs_strand.objects.filter(
            id=int(self.kwargs["strand_id"])).first()
        if self.getStrand and not self.getStrand.is_deleted:
            # if strand_id exist and not deleted
            return super().dispatch(request, *args, **kwargs)
        else:
            # if strand_id exist or deleted
            return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class delete_trackStrand(TemplateView):
    template_name = "adminportal/Shs_courses/delete_strand.html"

    def post(self, request, *args, **kwargs):
        self.deleteStrand.is_deleted = True
        self.deleteStrand.save()
        messages.success(
            request, f"{self.deleteStrand.strand_name} is deleted.")
        return HttpResponseRedirect(reverse("adminportal:view_courses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Remove Track Strand"
        context["track"] = self.deleteStrand.track.track_name
        context["strand_name"] = self.deleteStrand.strand_name
        context["definition"] = self.deleteStrand.definition
        return context

    def dispatch(self, request, *args, **kwargs):
        strand_id = self.kwargs["pk"]
        self.deleteStrand = shs_strand.objects.filter(
            id=int(self.kwargs["pk"])).exclude(is_deleted=True).first()
        if self.deleteStrand:
            # if strand_id exist and not deleted
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class view_schoolDocuments_canRequest(TemplateView):
    template_name = "adminportal/schoolDocuments/ListOfDocuments.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "School Documents Available"

        context["availableDocuments"] = studentDocument.activeObjects.values(
            "documentName", "id")

        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class addEditDocument(FormView):
    template_name = "adminportal/schoolDocuments/documentDetails.html"
    success_url = "/School_admin/schoolDocuments/"
    form_class = makeDocument

    def form_valid(self, form):
        documentName = form.cleaned_data["documentName"]
        try:
            if "docuId" in self.kwargs:
                # If editing the document
                self.docuObj.documentName = documentName
                self.docuObj.save()
                messages.success(self.request, "Updated Successfully.")
                return super().form_valid(form)

            else:
                # if adding a document
                self.docuObj = studentDocument.objects.filter(
                    documentName=documentName, is_active=False).first()
                if self.docuObj:
                    # If the document name exist but no longer active, then reactivate it.
                    self.docuObj.is_active = True
                    self.docuObj.save()
                else:
                    # if the document name does not exist or unique, then insert it.
                    studentDocument.objects.create(documentName=documentName)
                messages.success(self.request, "Added successfully.")
                return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, f"{documentName} already exist.")
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, "Error has occurred while saving. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        if "docuId" in self.kwargs:
            initial["documentName"] = self.docuObj.documentName
        return initial

    def dispatch(self, request, *args, **kwargs):
        try:
            if "docuId" in self.kwargs:
                self.docuObj = studentDocument.activeObjects.filter(
                    pk=int(self.kwargs["docuId"])).first()
                if self.docuObj:
                    return super().dispatch(request, *args, **kwargs)
                messages.warning(request, "Document does not exist.")
                return HttpResponseRedirect(reverse("adminportal:schoolDocuments"))
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            return HttpResponseRedirect(reverse("adminportal:schoolDocuments"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add/Edit Document"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class hideDocument(TemplateView):
    template_name = "adminportal/schoolDocuments/hideDocumentConfirmation.html"
    http_method_names = ["get", "post"]

    def post(self, request, *args, **kwargs):
        try:
            self.hideThisObj.is_active = False
            self.hideThisObj.save()
            messages.success(request, "Document is now hidden.")
            return HttpResponseRedirect(reverse("adminportal:schoolDocuments"))
        except Exception as e:
            messages.warning(request, e)
            return HttpResponseRedirect(reverse("adminportal:schoolDocuments"))

    def dispatch(self, request, *args, **kwargs):
        if studentDocument.activeObjects.filter(pk=int(self.kwargs["pk"])).exists():
            self.hideThisObj = studentDocument.objects.get(
                pk=int(self.kwargs["pk"]))
            return super().dispatch(request, *args, **kwargs)
        messages.warning(request, "Document does not exist.")
        return HttpResponseRedirect(reverse("adminportal:schoolDocuments"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Hide Document"
        context["documentName"] = self.hideThisObj.documentName
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class get_ongoingSchoolEvents(TemplateView, DeletionMixin):
    template_name = "adminportal/schoolEvents/ongoingSchoolEvents.html"
    http_method_names = ["get", "post"]
    success_url = "/School_admin/school_events/"

    def delete(self, request, *args, **kwargs):
        try:
            self.cancelThisEvent.is_cancelled = True
            self.cancelThisEvent.save()
        except Exception as e:
            pass
        return HttpResponseRedirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if ("pk" in request.POST) and request.method == "POST":
            self.cancelThisEvent = school_events.ongoingEvents.filter(
                id=int(request.POST["pk"])).first()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ongoing Events"

        get_eventsObj = school_events.ongoingEvents.annotate(
            can_cancel=Case(When(start_on__gt=date.today(),
                            then=Value(True)), default=Value(False))
        )

        if get_eventsObj:
            dct = dict()
            for event in get_eventsObj:
                if event.start_on.strftime("%B") not in dct:
                    dct[event.start_on.strftime("%B")] = list()
                    dct[event.start_on.strftime("%B")].append(event)
                else:
                    dct[event.start_on.strftime("%B")].append(event)
            context["events"] = dct

        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_schoolEvent(FormView):
    template_name = "adminportal/schoolEvents/newEvent.html"
    success_url = "/School_admin/school_events/"
    form_class = addEventForm

    def form_valid(self, form):
        try:
            name = form.cleaned_data["name"]
            start_on = form.cleaned_data["start_on"]
            school_events.objects.create(name=name, start_on=start_on)
            messages.success(self.request, "New event is added successfully")
            return super().form_valid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New event"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class edit_schoolEvent(FormView):
    template_name = "adminportal/schoolEvents/updateEvent.html"
    success_url = "/School_admin/school_events/"
    form_class = updateEventForm

    def form_valid(self, form):
        try:
            if form.has_changed():

                if "name" in form.changed_data and school_events.ongoingEvents.filter(name__unaccent__icontains=form.cleaned_data["name"]).exclude(id=self.get_event.id).exists():
                    messages.warning(
                        self.request, f"{form.cleaned_data['name']} is an ongoing event.")
                    return self.form_invalid(form)

                self.get_event.name = form.cleaned_data["name"]
                self.get_event.start_on = form.cleaned_data["start_on"]
                self.get_event.save()
                messages.success(self.request, "Event updated successfully.")
                return super().form_valid(form)
            return super().form_valid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["name"] = self.get_event.name
        initial["start_on"] = self.get_event.start_on
        return initial

    def dispatch(self, request, *args, **kwargs):
        try:
            self.get_event = school_events.ongoingEvents.filter(
                id=int(self.kwargs["pk"])).first()
            if self.get_event:
                return super().dispatch(request, *args, **kwargs)
            messages.warning(request, "Invalid Primary key.")
            return HttpResponseRedirect(reverse("adminportal:get_ongoingSchoolEvents"))
        except Exception as e:
            return HttpResponseRedirect(reverse("adminportal:get_ongoingSchoolEvents"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit event"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_subjects(FormView):
    template_name = "adminportal/subjects/subjectDetails.html"
    success_url = "/School_admin/subjects/"
    form_class = addSubjectForm

    def form_valid(self, form):
        try:
            code = form.cleaned_data["code"]
            title = form.cleaned_data["title"]
            if code and title:
                if subjects.objects.filter(code=code, title=title).exclude(is_remove=False).exists():
                    obj = subjects.objects.get(code=code, title=title)
                    obj.code = code
                    obj.title = title
                    obj.is_remove = False
                    obj.save()
                    return super().form_valid(form)

                subjects.objects.create(code=code, title=title)
                messages.success(
                    self.request, f"{code}: {title} is a new subject.")
                return super().form_valid(form)
            else:
                messages.warning(self.request, "Fill all fields.")
                return self.form_invalid(form)
        except IntegrityError:
            messages.warning(
                self.request, "Subject code or title already exist.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Subject"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class get_subjects(ListView):
    allow_empty = True
    context_object_name = "subjects"
    paginate_by = 15
    template_name = "adminportal/subjects/viewSubjects.html"

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("adminportal:getSubjects", kwargs={"key": request.POST.get("key")}))

    def get_queryset(self):
        try:
            if "key" in self.kwargs:
                qs = subjects.activeSubjects.values("id", "code", "title").filter(Q(code__unaccent__icontains=str(
                    self.kwargs["key"])) | Q(title__unaccent__icontains=str(self.kwargs["key"])))
            else:
                qs = subjects.activeSubjects.values("id", "code", "title")
        except Exception as e:
            messages.error(self.request, e)
            qs = subjects.objects.none()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "View Subjects"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class update_subjects(FormView):
    template_name = "adminportal/subjects/subjectDetails.html"
    success_url = "/School_admin/subjects/"
    form_class = addSubjectForm

    def form_valid(self, form):
        try:
            self.getSubject.refresh_from_db()
            if "removeSub" in self.request.POST:
                self.getSubject.is_remove = True
                self.getSubject.save()
                return super().form_valid(form)

            code = form.cleaned_data["code"]
            title = form.cleaned_data["title"]
            self.getSubject.code = code
            self.getSubject.title = title
            self.getSubject.save()
            return super().form_valid(form)
        except IntegrityError:
            messages.warning(self.request, "Subject already exist.")
            return self.form_invalid(form)
        except Exception as e:
            return self.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial["code"] = self.getSubject.code
        initial["title"] = self.getSubject.title
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Subject"
        context["for_update"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        self.getSubject = subjects.activeSubjects.filter(
            id=int(kwargs["pk"])).first()
        if self.getSubject:
            return super().dispatch(request, *args, **kwargs)
        messages.warning(request, "Subject Id does not exist.")
        return HttpResponseRedirect(reverse("adminportal:getSubjects"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class view_curriculum(ListView):
    allow_empty = True
    context_object_name = "curriculums"
    paginate_by = 1
    template_name = "adminportal/curriculum/getCurriculum.html"

    def get_queryset(self):
        try:
            qs = curriculum.allObjects.prefetch_related(
                Prefetch("g11_firstSem_subjects", queryset=subjects.objects.all(
                ), to_attr="g11FirstSemSubs"),
                Prefetch("g11_secondSem_subjects", queryset=subjects.objects.all(
                ), to_attr="g11SecondSemSubs"),
                Prefetch("g12_firstSem_subjects", queryset=subjects.objects.all(
                ), to_attr="g12FirstSemSubs"),
                Prefetch("g12_secondSem_subjects", queryset=subjects.objects.all(
                ), to_attr="g12SecondSemSubs"),
            ).annotate(
                can_edit=Case(When(effective_date__gte=date.today(),
                              then=Value(True)), default=Value(False))
            )
        except Exception as e:
            qs = curriculum.objects.none()
            messages.error(self.request, e)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "List of Curriculum"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_curriculum(SessionWizardView):
    templates = {
        "g11_firstSem": "adminportal/curriculum/addCurriculumHTMLfiles/g11firstsem.html",
        "g11_secondSem": "adminportal/curriculum/addCurriculumHTMLfiles/g11secondsem.html",
        "g12_firstSem": "adminportal/curriculum/addCurriculumHTMLfiles/g12firstsem.html",
        "g12_secondSem": "adminportal/curriculum/addCurriculumHTMLfiles/g12secondsem.html",
    }

    form_list = [
        ("g11_firstSem", g11_firstSem),
        ("g11_secondSem", g11_secondSem),
        ("g12_firstSem", g12_firstSem),
        ("g12_secondSem", g12_secondSem),
    ]

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        try:
            g11_First_Sem = self.get_cleaned_data_for_step("g11_firstSem")
            g11_Second_Sem = self.get_cleaned_data_for_step("g11_secondSem")
            g12_First_Sem = self.get_cleaned_data_for_step("g12_firstSem")
            g12_Second_Sem = self.get_cleaned_data_for_step("g12_secondSem")

            new_curriculum = curriculum()
            new_curriculum.effective_date = g11_First_Sem["effective_date"]
            new_curriculum.strand = shs_strand.objects.filter(
                pk=int(g11_First_Sem["strand"])).first()
            new_curriculum.save()

            new_curriculum.g11_firstSem_subjects.add(
                *g11_First_Sem["g11_firstSem_subjects"])
            new_curriculum.g11_secondSem_subjects.add(
                *g11_Second_Sem["g11_secondSem_subjects"])
            new_curriculum.g12_firstSem_subjects.add(
                *g12_First_Sem["g12_firstSem_subjects"])
            new_curriculum.g12_secondSem_subjects.add(
                *g12_Second_Sem["g12_secondSem_subjects"])
            new_curriculum.save()

            messages.success(
                self.request, "New curriculum is saved successfully.")

            return HttpResponseRedirect(reverse("adminportal:view_curriculum"))
        except Exception as e:
            return HttpResponseRedirect(reverse("adminportal:add_curriculum"))

    def render_goto_step(self, goto_step, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(
                self.steps.current, self.process_step(form))
            self.storage.set_step_files(
                self.steps.current, self.process_step_files(form))
        return super().render_goto_step(goto_step, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context['title'] = "New Curriculum"
        return context

    def dispatch(self, request, *args, **kwargs):
        if subjects.activeSubjects.all():
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.warning(request, "Add subjects to create curriculum.")
            return HttpResponseRedirect(reverse("adminportal:addSubjects"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class update_curriculum(SessionWizardView):
    templates = {
        "g11_firstSem": "adminportal/curriculum/addCurriculumHTMLfiles/g11firstsem.html",
        "g11_secondSem": "adminportal/curriculum/addCurriculumHTMLfiles/g11secondsem.html",
        "g12_firstSem": "adminportal/curriculum/addCurriculumHTMLfiles/g12firstsem.html",
        "g12_secondSem": "adminportal/curriculum/addCurriculumHTMLfiles/g12secondsem.html",
    }

    form_list = [
        ("g11_firstSem", g11_firstSem),
        ("g11_secondSem", g11_secondSem),
        ("g12_firstSem", g12_firstSem),
        ("g12_secondSem", g12_secondSem),
    ]

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)

        match step:
            case "g11_firstSem":
                initial["effective_date"] = self.get_saved_curriculum.effective_date
                initial["strand"] = str(self.get_saved_curriculum.strand.id)
                initial["g11_firstSem_subjects"] = tuple(
                    [item.id for item in self.get_saved_curriculum.g11_firstSem_subjects.all()])

            case "g11_secondSem":
                initial["g11_secondSem_subjects"] = tuple(
                    [item.id for item in self.get_saved_curriculum.g11_secondSem_subjects.all()])

            case "g12_firstSem":
                initial["g12_firstSem_subjects"] = tuple(
                    [item.id for item in self.get_saved_curriculum.g12_firstSem_subjects.all()])

            case "g12_secondSem":
                initial["g12_secondSem_subjects"] = tuple(
                    [item.id for item in self.get_saved_curriculum.g12_secondSem_subjects.all()])

        return initial

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        try:
            g11_First_Sem = self.get_cleaned_data_for_step("g11_firstSem")
            g11_Second_Sem = self.get_cleaned_data_for_step("g11_secondSem")
            g12_First_Sem = self.get_cleaned_data_for_step("g12_firstSem")
            g12_Second_Sem = self.get_cleaned_data_for_step("g12_secondSem")

            self.get_saved_curriculum.refresh_from_db()
            self.get_saved_curriculum.effective_date = g11_First_Sem["effective_date"]
            self.get_saved_curriculum.strand = shs_strand.objects.filter(
                pk=int(g11_First_Sem["strand"])).first()
            self.get_saved_curriculum.g11_firstSem_subjects.set(
                [*g11_First_Sem["g11_firstSem_subjects"]])
            self.get_saved_curriculum.g11_secondSem_subjects.set(
                [*g11_Second_Sem["g11_secondSem_subjects"]])
            self.get_saved_curriculum.g12_firstSem_subjects.set(
                [*g12_First_Sem["g12_firstSem_subjects"]])
            self.get_saved_curriculum.g12_secondSem_subjects.set(
                [*g12_Second_Sem["g12_secondSem_subjects"]])
            self.get_saved_curriculum.save()

            return HttpResponseRedirect(reverse("adminportal:view_curriculum"))
        except Exception as e:
            messages.error(self.request, e)
            return HttpResponseRedirect(reverse("adminportal:add_curriculum"))

    def render_goto_step(self, goto_step, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(
                self.steps.current, self.process_step(form))
            self.storage.set_step_files(
                self.steps.current, self.process_step_files(form))
        return super().render_goto_step(goto_step, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context['title'] = "Update Curriculum"
        return context

    def dispatch(self, request, *args, **kwargs):
        self.get_saved_curriculum = curriculum.allObjects.filter(
            pk=int(kwargs["pk"])).exclude(effective_date__lt=date.today()).first()
        if self.get_saved_curriculum and subjects.activeSubjects.all():
            return super().dispatch(request, *args, **kwargs)
        else:
            if not subjects.activeSubjects.all():
                messages.warning(request, "Add subjects to create curriculum.")
            return HttpResponseRedirect(reverse("adminportal:view_curriculum"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class make_section(FormView):
    template_name = "adminportal/schoolSection/makeSections.html"
    success_url = "/School_admin/Sections/"
    form_class = makeSectionForm

    def check_for_sections(self, sy, yl):
        self.latest_section = schoolSections.latestSections.filter(
            sy=sy, assignedStrand=self.this_curriculum.strand, yearLevel=yl).first()
        if self.latest_section:
            return self.latest_section.name[-1]
        else:
            return False

    def custom_ascii_range(self, start):
        start_index = ascii_uppercase.index(start)
        ascii_range = [value for key, value in enumerate(
            ascii_uppercase) if key > start_index]
        return ''.join(ascii_range)

    def form_valid(self, form):
        try:
            numberOfSection = int(form.cleaned_data["numberOfSection"])
            self.this_curriculum = curriculum.objects.filter(
                strand__id=int(form.cleaned_data['strand'])).first()
            self.sy = schoolYear.objects.filter(
                until__gte=date.today()).first()
            yearLevel = str(form.cleaned_data["yearLevel"])

            if self.check_for_sections(self.sy, yearLevel):
                asp = self.custom_ascii_range(
                    self.check_for_sections(self.sy, yearLevel))
            else:
                asp = ascii_uppercase

            for a, b in zip(asp, range(1, numberOfSection+1)):
                new_section = schoolSections()
                new_section.name = f"{form.cleaned_data['yearLevel']}-{self.get_strand(int(form.cleaned_data['strand']))}-{a}"
                new_section.yearLevel = form.cleaned_data['yearLevel']
                new_section.sy = self.sy
                new_section.assignedStrand = self.this_curriculum.strand
                new_section.allowedPopulation = int(
                    form.cleaned_data['allowedPopulation'])
                new_section.save()
                new_section.refresh_from_db()

                # new_section.first_sem_subjects.add(*self.get_curriculumSubjects(self.this_curriculum))
                # new_section.second_sem_subjects.add(*self.get_curriculumSubjects(self.this_curriculum))

                if str(form.cleaned_data["yearLevel"]) == "11":
                    new_section.first_sem_subjects.add(
                        *self.this_curriculum.g11_firstSem_subjects.all())
                    new_section.second_sem_subjects.add(
                        *self.this_curriculum.g11_secondSem_subjects.all())
                else:
                    new_section.first_sem_subjects.add(
                        *self.this_curriculum.g12_firstSem_subjects.all())
                    new_section.second_sem_subjects.add(
                        *self.this_curriculum.g12_secondSem_subjects.all())

                new_section.save()

            messages.success(self.request, "Sections created successfully.")
            if self.create_schedule(yearLevel, self.this_curriculum.strand.id):
                return super().form_valid(form)
            else:
                return HttpResponseRedirect(reverse("adminportal:generate_classSchedule"))
        except IntegrityError:
            messages.error(self.request, "Section already exist.")
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

    def create_schedule(self, yearLevel, strand_id):
        self.getschedule = schoolSections.latestSections.alias(count1Subjects=Count("first_sem_subjects"), count2Subjects=Count("second_sem_subjects"), sem1Scheds=Count("firstSemSched", filter=Q(firstSemSched__time_in__isnull=False, firstSemSched__time_out__isnull=False)), sem2Scheds=Count("firstSemSched", filter=Q(
            secondSemSched__time_in__isnull=False, secondSemSched__time_out__isnull=False))).exclude(Q(count1Subjects__lt=F('sem1Scheds')) | Q(count1Subjects__gt=F('sem1Scheds')), Q(count2Subjects__lt=F('sem2Scheds')) | Q(count2Subjects__gt=F('sem2Scheds'))).filter(yearLevel=yearLevel, assignedStrand__id=strand_id).first()
        if self.getschedule:
            firstSemesterSchedule = [[sched.time_in, sched.time_out]
                                     for sched in self.getschedule.firstSemSched.all()]
            secondSemesterSchedule = [[sched.time_in, sched.time_out]
                                      for sched in self.getschedule.secondSemSched.all()]
            getSectionWithNoSched = schoolSections.latestSections.alias(count1Subjects=Count("first_sem_subjects"), count2Subjects=Count("second_sem_subjects"), sem1Scheds=Count("firstSemSched", filter=Q(firstSemSched__time_in__isnull=True, firstSemSched__time_out__isnull=True)), sem2Scheds=Count("firstSemSched", filter=Q(
                secondSemSched__time_in__isnull=True, secondSemSched__time_out__isnull=True))).exclude(Q(count1Subjects__lt=F('sem1Scheds')) | Q(count1Subjects__gt=F('sem1Scheds')), Q(count2Subjects__lt=F('sem2Scheds')) | Q(count2Subjects__gt=F('sem2Scheds'))).filter(yearLevel=yearLevel, assignedStrand__id=strand_id)

            if self.save_schedule(self.generate_schedule([firstSemesterSchedule, secondSemesterSchedule], getSectionWithNoSched.count()), getSectionWithNoSched):
                return True
            else:
                return False
        return False

    def generate_schedule(self, initial_scheds, count_section):
        new_schedule = []
        private_sched = initial_scheds

        for section in range(count_section):
            # for each section
            new_schedule.append([])
            for key, semester in enumerate(initial_scheds):
                # for each semester
                new_schedule[section].append([])
                for id, subjectSchedule in enumerate(semester):
                    # for each schedule for a semester. A semester is a list that contains a pair of time-in and time-out on a list.
                    if id == (len(semester)-1):
                        new_schedule[section][key].append(
                            private_sched[key][0])
                    else:
                        new_schedule[section][key].append(
                            private_sched[key].pop(0))
                        private_sched[key].append(
                            new_schedule[section][key][id])

        # new_schedule data structures = [ [[[time-in, time-out], [time-in, time-out], [time-in, time-out]], [[time-in, time-out], [time-in, time-out]]], [[], []] ]
        return new_schedule

    def save_schedule(self, generatedSchedules, strand_sections):
        try:
            for key, value in enumerate(strand_sections):
                firstSemSchedule.save_sched(
                    value.firstSemSched.all(), generatedSchedules[key][0])
                secondSemSchedule.save_sched(
                    value.secondSemSched.all(), generatedSchedules[key][1])
            return True
        except Exception as e:
            messages.error(self.request, e)
            return False

    def get_strand(self, pk):
        strand_name = shs_strand.objects.filter(id=pk).first()
        return strand_name.strand_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New Section"
        return context

    def dispatch(self, request, *args, **kwargs):
        if schoolYear.objects.filter(until__gte=date.today()).exists():
            # Must have an ongoing school year
            return super().dispatch(request, *args, **kwargs)
        messages.warning(request, "Must have school year to create sections.")
        return HttpResponseRedirect(reverse("adminportal:index"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class get_sections(TemplateView):
    template_name = "adminportal/schoolSection/getSections.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "List of Sections"

        sections = schoolSections.latestSections.filter(yearLevel=int(self.kwargs["year"])).prefetch_related(Prefetch("firstSemSched", queryset=firstSemSchedule.objects.all(
        ), to_attr="firstSemesterSubjects"), Prefetch("secondSemSched", queryset=secondSemSchedule.objects.all(), to_attr="secondSemesterSubjects"))
        if sections:
            dct = dict()
            for section in sections:
                if section.assignedStrand.definition not in dct:
                    dct[section.assignedStrand.definition] = list()
                    dct[section.assignedStrand.definition].append(section)
                else:
                    dct[section.assignedStrand.definition].append(section)
            context["sections"] = dct
            context["yearLevel"] = sections[0].get_yearLevel_display()

        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            if self.kwargs["year"] == "11" or self.kwargs["year"] == "12":
                return super().dispatch(request, *args, **kwargs)
            return HttpResponseRedirect(reverse("adminportal:get_sections", kwargs={"year": "11"}))
        except Exception as e:
            return HttpResponseRedirect(reverse("adminportal:get_sections", kwargs={"year": "11"}))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class generate_classSchedule(FormView):
    # Generate class schedule for all latest section from the given strand
    template_name = "adminportal/schoolSection/generateSchedule.html"
    success_url = "/School_admin/Sections/"
    form_class = generate_schedule

    def count_FirstSemSubjects(self, strand):
        return self.this_curriculum.g11_firstSem_subjects.count() if int(strand) == 11 else self.this_curriculum.g12_firstSem_subjects.count()

    def count_SecondSemSubjects(self, strand):
        return self.this_curriculum.g11_secondSem_subjects.count() if int(strand) == 11 else self.this_curriculum.g12_secondSem_subjects.count()

    def get_semSubs(self, strand):
        if int(strand) == 11:
            firstSem_subs = self.this_curriculum.g11_firstSem_subjects.all()
            secondSem_subs = self.this_curriculum.g11_secondSem_subjects.all()
        else:
            firstSem_subs = self.this_curriculum.g12_firstSem_subjects.all()
            secondSem_subs = self.this_curriculum.g12_secondSem_subjects.all()
        return [firstSem_subs, secondSem_subs]

    def initialize_class_schedule(self, start_time, minutes_per_subjects, semesters):
        first_sem = [[start_time.time(), self.get_next_time(start_time, minutes_per_subjects[0])] if key == 0 else [self.get_next_time(
            start_time, minutes_per_subjects[0]*key), self.get_next_time(start_time, minutes_per_subjects[0]*(key+1))] for key, subject in enumerate(semesters[0])]
        second_sem = [[start_time.time(), self.get_next_time(start_time, minutes_per_subjects[1])] if key == 0 else [self.get_next_time(
            start_time, minutes_per_subjects[1]*key), self.get_next_time(start_time, minutes_per_subjects[1]*(key+1))] for key, subject in enumerate(semesters[1])]

        # for key, subject in enumerate(semesters[0]):
        #     if key == 0:
        #         first_sem.append((start_time.time(), self.get_next_time(
        #             start_time, minutes_per_subjects[0])))
        #     else:
        #         self.get_next_time((start_time, minutes_per_subjects[0]*key), self.get_next_time(
        #             start_time, minutes_per_subjects[0]*(key+1)))

        # for key, subject in enumerate(semesters[1]):
        #     if key == 0:
        #         second_sem.append((start_time.time(), self.get_next_time(
        #             start_time, minutes_per_subjects[1])))
        #     else:
        #         second_sem.append((self.get_next_time(
        #             start_time, minutes_per_subjects[1]*key), self.get_next_time(start_time, minutes_per_subjects[1]*(key+1))))

        return [first_sem, second_sem]

    def get_next_time(self, start_time, add_minutes):
        return datetime.strptime((start_time + timedelta(minutes=add_minutes)).strftime("%H:%M:%S"), "%H:%M:%S").time()

    def count_section(self, strand, yearLevel):
        self.strand_sections = schoolSections.latestSections.filter(yearLevel=yearLevel, assignedStrand__id=int(
            strand)).prefetch_related("first_sem_subjects", "second_sem_subjects")
        return schoolSections.latestSections.filter(yearLevel=yearLevel, assignedStrand__id=int(strand)).count()

    def generate_schedule(self, initial_scheds, strand, yearLevel):
        count_section = self.count_section(strand, yearLevel)
        new_schedule = []
        private_sched = initial_scheds

        for section in range(count_section):
            # for each section
            new_schedule.append([])
            for key, semester in enumerate(initial_scheds):
                # for each semester
                new_schedule[section].append([])
                for id, subjectSchedule in enumerate(semester):
                    # for each schedule for a semester. A semester is a list that contains a pair of time-in and time-out on a list.
                    if id == (len(semester)-1):
                        new_schedule[section][key].append(
                            private_sched[key][0])
                    else:
                        new_schedule[section][key].append(
                            private_sched[key].pop(0))
                        private_sched[key].append(
                            new_schedule[section][key][id])

        # new_schedule data structures = [ [[[time-in, time-out], [time-in, time-out], [time-in, time-out]], [[time-in, time-out], [time-in, time-out]]], [[], []] ]
        return new_schedule

    def save_schedule(self, generatedSchedules):
        try:
            for key, value in enumerate(self.strand_sections):
                firstSemSchedule.save_sched(
                    value.firstSemSched.all(), generatedSchedules[key][0])
                secondSemSchedule.save_sched(
                    value.secondSemSched.all(), generatedSchedules[key][1])
            return True
        except Exception as e:
            messages.error(self.request, e)
            return False

    def form_valid(self, form):
        try:
            strand = form.cleaned_data["strand"]
            class_hours = int(form.cleaned_data["class_hours"])
            start_time = datetime.strptime(
                str(form.cleaned_data["start_time"]), "%H:%M:%S")

            # strand[2:4] - will display the strand yearlevel
            # strand[6:8] - will display the strand id

            self.this_curriculum = curriculum.objects.get(
                strand__id=int(strand[6:8]))

            number_of_subjects_perSem = [self.count_FirstSemSubjects(
                strand[2:4]), self.count_SecondSemSubjects(strand[2:4])]

            minutes_per_subjects = [(class_hours * 60)/number_of_subjects_perSem[0],
                                    (class_hours * 60)/number_of_subjects_perSem[1]]

            initial_scheds = self.initialize_class_schedule(
                start_time, minutes_per_subjects, self.get_semSubs(strand[2:4]))

            generated_schedule = self.generate_schedule(
                initial_scheds, strand[6:8], strand[2:4])

            if self.save_schedule(generated_schedule):
                messages.success(self.request, "New schedule is saved.")

            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Generate Class Schedule"
        return context

    def dispatch(self, request, *args, **kwargs):
        if schoolSections.latestSections.all():
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.warning(
                request, "Must have sections from latest school year.")
            return HttpResponseRedirect(reverse("adminportal:new_section"))
