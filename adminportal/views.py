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
from datetime import date, datetime
from . forms import *
from . models import *
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import Q, FilteredRelation, Prefetch, Count, Case, When, Value
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.exceptions import ObjectDoesNotExist
import re


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


def strand_dispatch_func(request, strand_id):
    obj = shs_strand.objects.filter(id=strand_id).first()
    if obj:
        if obj.is_deleted == True:
            messages.warning(
                request, "Strand id no. %s no longer exist." % strand_id)
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
    else:
        messages.error(request, "Strand id no. %s does not exist." % strand_id)
        return HttpResponseRedirect(reverse("adminportal:view_courses"))


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
class add_shs_track_cbv(FormView):
    template_name = "adminportal/Shs_courses/create_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

    def get_success_url(self):
        if "another" in self.request.POST:
            return "/School_admin/Courses/add_track/"
        else:
            return super().get_success_url()

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        details = form.cleaned_data["details"]

        if name and details:
            try:
                if shs_track.objects.filter(track_name=name, is_deleted=False).exists():
                    messages.warning(
                        self.request, "%s already exist." % name)
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
                    shs_track.objects.create(
                        track_name=name, definition=details)
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
        else:
            messages.warning(self.request, "Fill all fields.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Track"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class edit_track(FormView):
    template_name = "adminportal/Shs_courses/edit_track.html"
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

        if form.has_changed():
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
        else:
            return super().form_valid(form)

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


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class delete_track(TemplateView):
    template_name = "adminportal/Shs_courses/delete_track.html"

    def post(self, request, *args, **kwargs):
        obj = shs_track.objects.filter(id=self.kwargs["pk"]).first()
        obj.is_deleted = True
        obj.save()

        foreign_obj = shs_strand.objects.filter(track=obj)
        for item in foreign_obj:
            item.is_deleted = True
            item.save()

        messages.success(request, "%s is deleted successfully." %
                         obj.track_name)
        return HttpResponseRedirect(reverse("adminportal:view_courses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["obj"] = shs_track.objects.filter(id=self.kwargs["pk"]).first()
        context["related_strands"] = shs_strand.objects.filter(
            track__id=self.kwargs["pk"])
        return context

    def dispatch(self, request, *args, **kwargs):
        if shs_track.objects.filter(id=self.kwargs["pk"], is_deleted=True).exists():
            # if track is already deleted
            messages.warning(
                request, "Course Track with id no. %s no longer exist." % self.kwargs["pk"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        elif not shs_track.objects.filter(id=self.kwargs["pk"]).exists():
            # if track id does not exist
            messages.warning(
                request, "Course Track with id no. %s does not exist." % self.kwargs["pk"])
            return HttpResponseRedirect(reverse("adminportal:view_courses"))
        else:
            # if track id is not yet deleted
            return super().dispatch(request, *args, **kwargs)


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class add_strand(FormView):
    success_url = "/School_admin/Courses/"
    form_class = add_strand_form
    template_name = "adminportal/Shs_courses/create_strands.html"

    def get_success_url(self):
        if "another" in self.request.POST:
            return "/School_admin/Courses/Add_strand/" + self.kwargs["track_id"]
        else:
            return super().get_success_url()

    def form_valid(self, form):
        strand_name = form.cleaned_data["strand_name"]
        strand_details = form.cleaned_data["strand_details"]

        if form.has_changed():
            if strand_name and strand_details:
                # if not empty
                try:
                    obj1 = shs_strand.objects.filter(
                        strand_name=strand_name).first()
                    foreign_obj = shs_track.objects.get(
                        id=self.kwargs["track_id"])
                    if obj1:
                        # if strand name already exist
                        if obj1.is_deleted == False:
                            # if the existing strand name is not deleted
                            messages.warning(
                                self.request, "%s already exist." % strand_name)
                            return self.form_invalid(form)
                        else:
                            # if the existing strand is deleted=True
                            obj_update = shs_strand.objects.filter(strand_name=strand_name).update(
                                track=foreign_obj,
                                strand_name=strand_name,
                                definition=strand_details,
                                is_deleted=False
                            )
                            messages.success(self.request, "%s is added to %s" % (
                                strand_name, foreign_obj.track_name))
                            return super().form_valid(form)
                    else:
                        # If strand name is unique, then, Create new strand
                        shs_strand.objects.create(
                            track=foreign_obj,
                            strand_name=strand_name,
                            definition=strand_details,
                        )
                        messages.success(self.request, "%s is added to %s" % (
                            strand_name, foreign_obj.track_name))
                        return super().form_valid(form)
                except IntegrityError:
                    messages.warning(
                        self.request, "%s already exist." % strand_name)
                    return self.form_invalid(form)
                except Exception as e:
                    messages.error(self.request, e)
                    return self.form_valid(form)
            else:
                # if empty fields
                messages.warning(self.request, "Fill all fields")
                return self.form_invalid(form)
        else:
            return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        obj = shs_track.objects.filter(id=self.kwargs["track_id"]).first()
        initial["track"] = obj.track_name
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Strand"
        return context

    def dispatch(self, request, *args, **kwargs):
        track_id = self.kwargs["track_id"]

        if shs_track.objects.filter(id=track_id, is_deleted=False).exists():
            # if track_id is not deleted
            return super().dispatch(request, *args, **kwargs)
        else:
            if shs_track.objects.filter(id=track_id, is_deleted=True).exists():
                # if track_id exist but deleted
                messages.error(
                    request, "Track id no. %s no longer exist." % track_id)
                return HttpResponseRedirect(reverse("adminportal:view_courses"))

            # if there's no track_id
            messages.error(
                request, "Track id no. %s does not exist." % track_id)
            return HttpResponseRedirect(reverse("adminportal:view_courses"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class edit_strand(FormView):
    template_name = "adminportal/Shs_courses/edit_strand.html"
    form_class = edit_strand_form
    success_url = "/School_admin/Courses/"

    def form_valid(self, form):
        strand_name = form.cleaned_data["strand_name"]
        strand_details = form.cleaned_data["strand_details"]
        strand_id = self.kwargs["strand_id"]

        strand_obj = shs_strand.objects.filter(id=strand_id).first()
        if form.has_changed():
            if strand_name and strand_details:
                try:
                    strand_obj.strand_name = strand_name
                    strand_obj.definition = strand_details
                    strand_obj.save()
                    messages.success(
                        self.request, "%s is updated successfully." % strand_name)
                    return super().form_valid(form)
                except IntegrityError:
                    messages.warning(
                        self.request, "%s already exist." % strand_name)
                    return self.form_invalid(form)
                except Exception as e:
                    messages.error(self.request, e)
                    return self.form_invalid(form)
            else:
                messages.warning(self.request, "Fill all fields.")
                return self.form_invalid(form)
        else:
            return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        obj = shs_strand.objects.get(id=self.kwargs["strand_id"])
        initial["track"] = obj.track.track_name
        initial["strand_name"] = obj.strand_name
        initial["strand_details"] = obj.definition
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Strand"
        return context

    def dispatch(self, request, *args, **kwargs):
        strand_id = self.kwargs["strand_id"]

        if shs_strand.objects.filter(id=strand_id, is_deleted=False).exists():
            # if strand_id exist and not deleted
            return super().dispatch(request, *args, **kwargs)
        else:
            # if strand_id exist or deleted
            return strand_dispatch_func(request, strand_id)


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class delete_strand(TemplateView):
    template_name = "adminportal/Shs_courses/delete_strand.html"

    def post(self, request, *args, **kwargs):
        obj = shs_strand.objects.filter(id=self.kwargs["pk"]).first()
        obj.is_deleted = True
        obj.save()

        messages.success(request, "%s is deleted successfully." %
                         obj.strand_name)
        return HttpResponseRedirect(reverse("adminportal:view_courses"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = shs_strand.objects.get(id=self.kwargs["pk"])
        context["track"] = obj.track.track_name
        context["strand_name"] = obj.strand_name
        context["definition"] = obj.definition
        return context

    def dispatch(self, request, *args, **kwargs):
        strand_id = self.kwargs["pk"]

        if shs_strand.objects.filter(id=strand_id, is_deleted=False).exists():
            # if strand_id exist and not deleted
            return super().dispatch(request, *args, **kwargs)
        else:
            return strand_dispatch_func(request, strand_id)


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
