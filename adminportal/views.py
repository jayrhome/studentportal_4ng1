from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, FormMixin
from django.views.generic.detail import DetailView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, datetime
from . forms import add_shs_track, add_strand_form, edit_strand_form, ea_setup_form
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
    template_name = "adminportal/dashboard.html"


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class shs_courses(TemplateView):
    # View courses
    template_name = "adminportal/Shs_courses/courses.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Courses"
        context["courses"] = shs_track.objects.filter(is_deleted=False).prefetch_related(Prefetch(
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False), to_attr="strands"))

        return context


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class add_shs_track_cbv(FormView):
    template_name = "adminportal/Shs_courses/create_track.html"
    form_class = add_shs_track
    success_url = "/School_admin/Courses/"

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
        context["title"] = "Add Course"
        return context


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
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


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
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


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class add_strand(FormView):
    success_url = "/School_admin/Courses/"
    form_class = add_strand_form
    template_name = "adminportal/Shs_courses/create_strands.html"

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


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
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


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
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


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class admission_and_enrollment(TemplateView):
    template_name = "adminportal/AdmissionAndEnrollment/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date_now = date.today()
        add_year = add_school_year(date_now, 1)
        sy = " ".join(
            map(str, [date_now.strftime("%Y"), "-", add_year.strftime("%Y")]))

        context["enrollment_status"] = self.setup_verification(sy)
        context["sy"] = sy
        context["count_enrollment"] = ""

        return context

    def setup_verification(self, sy):
        if not enrollment_admission_setup.objects.filter(ea_setup_sy__sy=sy).exists():
            return "new"
        else:
            enrollment_obj = enrollment_admission_setup.objects.filter(
                ea_setup_sy__sy=sy)
            if enrollment_obj.is_visible and enrollment_obj.still_accepting:
                # If visible and still accepting request
                return "continue"
            elif not enrollment_obj.is_visible and enrollment_obj.still_accepting:
                # If not visible but still allowed to accept request
                return "pending"
            else:
                # if not visible and no longer allowed to accept request
                return "stop"
