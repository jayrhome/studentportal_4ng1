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
from . forms import *
from . models import *
from django.db import IntegrityError
from django.contrib import messages
from django.db.models import Q, FilteredRelation, Prefetch, Count
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


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
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False), to_attr="strands")).order_by("track_name")

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


# validate the latest school year
def validate_enrollmentSetup(request, sy):
    dt1 = date.today()
    dt2 = sy.date_created.date()
    dt3 = dt1 - dt2

    if dt3.days < 209:
        return True
    return False


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class admission_and_enrollment(TemplateView):
    template_name = "adminportal/AdmissionAndEnrollment/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            sy = school_year.objects.latest("date_created")
            context["sy"] = sy.sy

            if sy.setup_sy.start_date > date.today() and validate_enrollmentSetup(self.request, sy):
                # if school year is less than 209 days and setup form will start soon
                context["start_soon"] = True  # For update period button
                context["start_date"] = sy.setup_sy.start_date.strftime(
                    "%A, %b %d, %Y")
                context["end_date"] = sy.setup_sy.end_date.strftime(
                    "%A, %b %d, %Y")
                context["uid"] = urlsafe_base64_encode(
                    force_bytes(sy.setup_sy.id))

            elif sy.setup_sy.end_date >= date.today() and validate_enrollmentSetup(self.request, sy):
                # if school year is less than 209 days and setup form will end soon
                if sy.setup_sy.still_accepting:
                    # if enrollment is not postpone
                    context["is_empty_count"] = self.count_validation2(sy)
                    context["count_sy_details"] = self.count_validation1(sy)
                    context["is_extend"] = True  # extend period
                    context["end_dt"] = sy.setup_sy.end_date.strftime(
                        "%A, %b %d, %Y")

                    # use to postpone enrollment
                    context["stop_accepting"] = True
                    context["uid"] = urlsafe_base64_encode(
                        force_bytes(sy.setup_sy.id))

                else:
                    # if enrollment is postpone
                    context["is_empty_count"] = self.count_validation2(sy)
                    context["count_sy_details"] = self.count_validation1(sy)
                    context["stop_from_accepting"] = True
                    context["is_extend"] = True  # extend period
                    context["end_dt"] = sy.setup_sy.end_date.strftime(
                        "%A, %b %d, %Y")
                    context["uid"] = urlsafe_base64_encode(
                        force_bytes(sy.setup_sy.id))

            else:
                if sy.setup_sy.end_date <= date.today() and validate_enrollmentSetup(self.request, sy):
                    # if school year is less than 209 days and setup form period has ended
                    context["is_empty_count"] = self.count_validation2(sy)
                    context["count_sy_details"] = self.count_validation1(sy)
                    context["extend_notif"] = f"Enrollment and Admission for S.Y. {sy} have already ended."
                    context["uid"] = urlsafe_base64_encode(
                        force_bytes(sy.setup_sy.id))

            if not validate_enrollmentSetup(self.request, sy):
                # If school year is greater than 209 days.
                context["new_enrollment"] = True

        except:
            # if no school year
            # if with school year but no setup form
            context["no_record"] = True
        return context

    def count_validation2(self, sy):
        enrollment_count = Count(
            "sy_enrolled", filter=Q(sy_enrolled__is_deleted=False))
        admission_count_sy = Count(
            "sy_admitted", filter=Q(sy_admitted__is_deleted=False))
        count_if_exist = school_year.objects.filter(id=sy.id).annotate(
            e_count=enrollment_count, a_count=admission_count_sy).first()

        return False if count_if_exist.e_count or count_if_exist.a_count else True

    def count_validation1(self, sy):
        enrolled_count = Count(
            "sy_enrolled", filter=Q(sy_enrolled__is_passed=True, sy_enrolled__is_deleted=False))
        pending_enrollment_count = Count(
            "sy_enrolled", filter=Q(sy_enrolled__is_passed=False, sy_enrolled__is_deleted=False))
        admission_count = Count("sy_admitted", filter=Q(
            sy_admitted__is_validated=True, sy_admitted__is_deleted=False))
        pending_admission_count = Count(
            "sy_admitted", filter=Q(sy_admitted__is_validated=False, sy_admitted__is_deleted=False))

        return school_year.objects.filter(id=sy.id).annotate(enrolled_students=enrolled_count, pending_enrollment=pending_enrollment_count, admitted_students=admission_count, pending_admission=pending_admission_count).first()


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class update_enrollment(FormView):
    # If enrollment and admission will start soon
    form_class = ea_setup_form
    template_name = "adminportal/AdmissionAndEnrollment/update_enrollment.html"
    success_url = "/School_admin/Admission_and_enrollment/"

    def form_valid(self, form):
        try:
            if form.has_changed():
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
                if start_date < end_date:
                    enrollment_admission_setup.objects.filter(id=self.convert_to_pk(
                        self.kwargs["uid"])).update(start_date=start_date, end_date=end_date)
                    messages.success(
                        self.request, "Enrollment and Admission period is updated successfully.")
                    return super().form_valid(form)
                else:
                    messages.warning(
                        self.request, "Dates are not valid! Try again.")
                    return self.form_invalid(form)
            else:
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, e)
            return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        get_obj = enrollment_admission_setup.objects.get(
            id=self.convert_to_pk(self.kwargs["uid"]))
        initial["start_date"] = get_obj.start_date
        initial["end_date"] = get_obj.end_date
        return initial

    def dispatch(self, request, *args, **kwargs):
        try:
            uid = self.convert_to_pk(self.kwargs["uid"])
            get_obj = enrollment_admission_setup.objects.get(id=uid)
            if validate_enrollmentSetup(request, get_obj.ea_setup_sy):
                if get_obj.start_date > date.today() and get_obj.end_date > date.today():
                    return super().dispatch(request, *args, **kwargs)
                else:
                    messages.warning(
                        request, "Enrollment and Admission period are no longer valid.")
                    return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
            else:
                messages.warning(request, "%s is no longer valid." %
                                 get_obj.ea_setup_sy.sy)
                return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Date"
        context["setup_details"] = enrollment_admission_setup.objects.values(
            "ea_setup_sy__sy").get(id=self.convert_to_pk(self.kwargs["uid"]))
        return context

    def convert_to_pk(self, uid):
        return force_str(urlsafe_base64_decode(uid))


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class extend_enrollment(FormView):
    # for extend button
    # still_accepting will set to True
    form_class = extend_enrollment
    success_url = "/School_admin/Admission_and_enrollment/"
    template_name = "adminportal/AdmissionAndEnrollment/extend_enrollment.html"

    def form_valid(self, form):
        try:
            if form.has_changed():
                end_date = form.cleaned_data["end_date"]
                if end_date > date.today():
                    enrollment_admission_setup.objects.filter(id=self.convert_to_pk(
                        self.kwargs["uid"])).update(end_date=end_date, still_accepting=True)
                    get_enrollment = enrollment_admission_setup.objects.values(
                        'end_date').get(id=self.convert_to_pk(self.kwargs["uid"]))
                    messages.success(
                        self.request, "Enrollment and Admission period is successfully extended until %s." % get_enrollment["end_date"].strftime("%A, %b %d, %Y"))
                    return super().form_valid(form)
                else:
                    messages.warning(
                        self.request, "End date must be greater than date today.")
                    return self.form_invalid(form)
            else:
                get_obj = enrollment_admission_setup.objects.filter(
                    id=self.convert_to_pk(self.kwargs["uid"])).first()
                if not get_obj.still_accepting:
                    # if postpone
                    get_obj.still_accepting = True
                    get_obj.save()
                    messages.success(
                        self.request, "Enrollment and Admission is open again.")
                    return super().form_valid(form)
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, e)
            return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        get_obj = enrollment_admission_setup.objects.get(
            id=self.convert_to_pk(self.kwargs["uid"]))
        initial["end_date"] = get_obj.end_date
        return initial

    def dispatch(self, request, *args, **kwargs):
        try:
            get_obj = enrollment_admission_setup.objects.get(
                id=self.convert_to_pk(self.kwargs["uid"]))
            if validate_enrollmentSetup(request, get_obj.ea_setup_sy):
                if get_obj.start_date <= date.today():
                    return super().dispatch(request, *args, **kwargs)
                else:
                    messages.warning(
                        request, "You cannot extend the enrollment date using this function.")
                    return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
            else:
                # if school year creation date is greater than 209 days
                messages.warning(request, "%s is no longer valid." %
                                 get_obj.ea_setup_sy.sy)
                return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Extend Period"
        context["school_year"] = enrollment_admission_setup.objects.values(
            "ea_setup_sy__sy").get(id=self.convert_to_pk(self.kwargs["uid"]))
        return context

    def convert_to_pk(self, uid):
        return force_str(urlsafe_base64_decode(uid))


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class postpone_enrollment(TemplateView):
    template_name = "adminportal/AdmissionAndEnrollment/postpone_enrollment.html"

    def post(self, request, *args, **kwargs):
        try:
            get_enrollment = enrollment_admission_setup.objects.get(
                id=self.convert_to_pk(self.kwargs["uid"]))
            get_enrollment.still_accepting = False
            get_enrollment.save()
            messages.success(
                request, "Enrollment and Admission are now postponed.")
            return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))

    def dispatch(self, request, *args, **kwargs):
        try:
            get_obj = enrollment_admission_setup.objects.get(
                id=self.convert_to_pk(self.kwargs["uid"]))

            if validate_enrollmentSetup(request, get_obj.ea_setup_sy):
                if get_obj.start_date <= date.today() and get_obj.end_date >= date.today():
                    if get_obj.still_accepting:
                        return super().dispatch(request, *args, **kwargs)
                    else:
                        messages.warning(
                            request, "Enrollment and Admission are already postponed.")
                        return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
                else:
                    messages.warning(
                        request, "Enrollment and Admission period should have already started and not yet finished.")
                    return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
            else:
                messages.warning(request, "School year is no longer valid.")
                return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))

        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Postpone Enrollment"
        context["sy"] = enrollment_admission_setup.objects.values(
            'ea_setup_sy__sy').get(id=self.convert_to_pk(self.kwargs["uid"]))
        return context

    def convert_to_pk(self, uid):
        return force_str(urlsafe_base64_decode(uid))


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class open_enrollment_admission(FormView):
    template_name = "adminportal/AdmissionAndEnrollment/setup_enrollment.html"
    form_class = ea_setup_form
    success_url = "/School_admin/Admission_and_enrollment/"

    def form_valid(self, form):
        if form.has_changed():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            if start_date < end_date:
                try:
                    sy = school_year.objects.latest("date_created")
                    if validate_enrollmentSetup(self.request, sy):
                        obj_create_from_existing_obj = enrollment_admission_setup.objects.create(
                            ea_setup_sy=sy,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        messages.success(
                            self.request, "Setup Form for S.Y. %s is created successfully." % sy.sy)
                        return super().form_valid(form)
                    else:
                        obj_pure_create = enrollment_admission_setup.objects.create(
                            ea_setup_sy=school_year.objects.get_or_create(
                                sy=compute_schoolyear(1)
                            ),
                            start_date=start_date,
                            end_date=end_date,
                        )
                        messages.success(
                            self.request, "Setup Form for S.Y. %s is created successfully." % obj_pure_create.ea_setup_sy.sy)
                        return super().form_valid(form)
                except:
                    try:
                        obj_created = enrollment_admission_setup.objects.create(
                            ea_setup_sy=school_year.objects.create(
                                sy=compute_schoolyear(1)),
                            start_date=start_date,
                            end_date=end_date,
                        )
                        messages.success(
                            self.request, "S.Y. %s Enrollment and Admission Forms is created successfully." % obj_created.ea_setup_sy.sy)
                        return super().form_valid(form)
                    except Exception as e:
                        messages.error(self.request, e)
                        return self.form_invalid(form)
            else:
                messages.warning(
                    self.request, "Start date should be less than the End Date.")
                return self.form_invalid(form)
        else:
            messages.warning(self.request, "Fill all fields with valid data.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Setup Details"
        context["sy"] = self.sy_display()
        return context

    def sy_display(self):
        try:
            sy_obj = school_year.objects.latest("date_created")
            return sy_obj.sy if validate_enrollmentSetup(self.request, sy_obj) else compute_schoolyear(1)
        except:
            return compute_schoolyear(1)

    def dispatch(self, request, *args, **kwargs):
        try:
            sy = school_year.objects.latest("date_created")
            if validate_enrollmentSetup(request, sy):
                # if school year is less than 209 days since its creation
                try:
                    # If school_year has enrollment_admission_setup
                    get_sy_objs = enrollment_admission_setup.objects.get(
                        ea_setup_sy=sy)
                    messages.warning(
                        request, "You already have a setup form for S.Y. %s." % sy.sy)
                    return HttpResponseRedirect(reverse("adminportal:admission_and_enrollment"))
                except:
                    if request.method == "GET":
                        messages.warning(
                            request, "S.Y. %s has no admission and enrollment setup form. Create Now." % sy.sy)
                    return super().dispatch(request, *args, **kwargs)
            else:
                # If school_year is greater than 209 days since its creation
                return super().dispatch(request, *args, **kwargs)
        except:
            # if there's no data in school_year table
            return super().dispatch(request, *args, **kwargs)


@method_decorator([login_required(login_url="studentportal:login"), user_passes_test(superuser_only, login_url="teachersportal:index")], name="dispatch")
class view_admitted_students(TemplateView):
    pass
