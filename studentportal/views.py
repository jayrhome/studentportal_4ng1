from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Count, Q, Case, When, Value
from . forms import *
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from ratelimit.decorators import ratelimit
from adminportal.models import *
from formtools.wizard.views import SessionWizardView
from datetime import date, datetime
from smtplib import SMTPException
from usersPortal.models import user_photo
from . models import *
from . email_token import *

User = get_user_model()


def load_userPic(user):
    try:
        user_profilePicture = user_photo.objects.filter(
            photo_of=user.profile).only("image").first()
    except Exception as e:
        user_profilePicture = ""
    return user_profilePicture


def not_authenticated_user(user):
    return not user.is_authenticated


def student_and_anonymous(user):
    if user.is_authenticated:
        return user.is_student
    else:
        return True


def student_access_only(user):
    return user.is_student


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


@method_decorator(user_passes_test(student_and_anonymous, login_url="adminportal:index"), name="dispatch")
class index(TemplateView):
    template_name = "studentportal/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Newfangled Senior High School"

        context["courses"] = shs_track.objects.filter(is_deleted=False).prefetch_related(Prefetch(
            "track_strand", queryset=shs_strand.objects.filter(is_deleted=False).order_by("strand_name"), to_attr="strands")).order_by("track_name")

        context["contacts"] = school_contact_number.objects.filter(
            is_deleted=False).first()

        context["emails"] = school_email.objects.filter(
            is_deleted=False).first()

        # context["enroll_now"] = self.enroll_now(self.request)

        # context["sy"] = "S.Y. %s" % self.determine_valid_sy(
        # ) if self.determine_valid_sy() else False

        # if context["sy"]:
        #     # if the latest school year is valid
        #     if context["enroll_now"] == "enroll":
        #         context["end_date_enrollment"] = enrollment_admission_setup.objects.get(
        #             ea_setup_sy__sy=self.determine_valid_sy())
        #     elif context["enroll_now"] == "start_soon":
        #         context["start_date_enrollment"] = enrollment_admission_setup.objects.get(
        #             ea_setup_sy__sy=self.determine_valid_sy())
        #     else:
        #         pass

        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""

        return context

    def enroll_now(self, request):
        if request.user.is_authenticated:
            if request.user.is_student:
                try:
                    sy = school_year.objects.latest('date_created')
                    if validate_enrollmentSetup(request, sy):
                        if enrollment_admission_setup.objects.filter(ea_setup_sy=sy).exists():
                            # if the latest school year have admission setup
                            setup_obj = enrollment_admission_setup.objects.filter(
                                ea_setup_sy=sy).first()
                            if setup_obj.start_date <= date.today() and setup_obj.end_date >= date.today():
                                # If enrollment and admission dates are ongoing
                                if setup_obj.still_accepting:
                                    get_admission = student_admission_details.objects.filter(
                                        admission_owner__id=request.user.id).first()

                                    if get_admission:
                                        # If student have admission
                                        if get_admission.is_validated and not get_admission.is_denied:
                                            # if student admission is validated and not denied
                                            if not student_enrollment_details.objects.filter(admission_details=get_admission, enrolled_schoolyear=sy).exists():
                                                # if a valid admission have no enrollment on current school year
                                                return "enroll"
                                        else:
                                            if get_admission.admission_sy == sy:
                                                if not student_enrollment_details.objects.filter(admission_details=get_admission, enrolled_schoolyear=sy).exists():
                                                    # For student with not yet validated admission and no submitted enrollment
                                                    return "enroll"
                                            else:
                                                # For student with previous admission but not valid and school_year is previous, they can submit new admission
                                                return "enroll"
                                    else:
                                        # If the logged-in user have no admission
                                        return "enroll"
                                else:
                                    return "postpone"
                            elif setup_obj.start_date > date.today() and setup_obj.end_date > date.today():
                                return "start_soon"
                            else:
                                pass
                except:
                    pass
        else:
            # if anonymous user
            pass

    def determine_valid_sy(self):
        try:
            sy = school_year.objects.order_by('-date_created').first()
            if validate_enrollmentSetup(self.request, sy):
                return sy.sy
            return False
        except:
            return False


admission_templates = {
    "adm1": "studentportal/admission_HTMLs/admission_student_details.html",
    "adm2": "studentportal/admission_HTMLs/admission_elementary_details.html",
    "adm3": "studentportal/admission_HTMLs/admission_jhs_details.html",
}


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class admission_application(SessionWizardView):
    form_list = [("adm1", admission_personal_details),
                 ("adm2", elementary_school_details),
                 ("adm3", jhs_details)]

    def get_template_names(self):
        return [admission_templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        try:
            adm1 = self.get_cleaned_data_for_step("adm1")
            adm2 = self.get_cleaned_data_for_step("adm2")
            adm3 = self.get_cleaned_data_for_step("adm3")

            obj, created = student_admission_details.objects.update_or_create(
                admission_owner=self.request.user,
                defaults={
                    'admission_owner': self.request.user,
                    'first_name': adm1['first_name'],
                    'middle_name': adm1['middle_name'],
                    'last_name': adm1['last_name'],
                    'sex': adm1['sex'],
                    'date_of_birth': adm1['birth_date'],
                    'birthplace': adm1['birthplace'],
                    'nationality': adm1['nationality'],
                    'first_chosen_strand': shs_strand.objects.get(id=adm1["first_chosen_strand"]),
                    'second_chosen_strand': shs_strand.objects.get(id=adm1["second_chosen_strand"]),

                    'elem_name': adm2['elem_name'],
                    'elem_address': adm2['elem_address'],
                    'elem_region': adm2['elem_region'],
                    'elem_year_completed': adm2['elem_year_completed'],
                    'elem_pept_passer': adm2['elem_pept_passer'],
                    'elem_pept_date_completion': adm2['elem_pept_date_completion'] if adm2['elem_pept_passer'] else None,
                    'elem_ae_passer': adm2['elem_ae_passer'],
                    'elem_ae_date_completion': adm2['elem_ae_date_completion'] if adm2['elem_ae_passer'] else None,
                    'elem_community_learning_center': adm2['elem_community_learning_center'],
                    'elem_clc_address': adm2['elem_clc_address'],

                    'jhs_name': adm3['jhs_name'],
                    'jhs_address': adm3['jhs_address'],
                    'jhs_region': adm3['jhs_region'],
                    'jhs_year_completed': adm3['jhs_year_completed'],
                    'jhs_pept_passer': adm3['jhs_pept_passer'],
                    'jhs_pept_date_completion': adm3['jhs_pept_date_completion'] if adm3['jhs_pept_passer'] else None,
                    'jhs_ae_passer': adm3['jhs_ae_passer'],
                    'jhs_ae_date_completion': adm3['jhs_ae_date_completion'] if adm3['jhs_ae_passer'] else None,
                    'jhs_community_learning_center': adm3['jhs_community_learning_center'],
                    'jhs_clc_address': adm3['jhs_clc_address'],

                    'admission_sy': school_year.objects.latest("date_created"),
                    'is_validated': False,
                    'is_late': False,
                    'is_transferee': False,
                    'is_denied': False
                }
            )

            messages.success(
                self.request, "Your admission application is submitted. Kindly wait for a response from the admin.")
            return HttpResponseRedirect(reverse("studentportal:enrollment_application"))

        except Exception as e:
            messages.error(self.request, e)
            return HttpResponseRedirect(reverse("studentportal:index"))

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
        context['title'] = "Student Admission"

        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""

        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            sy = school_year.objects.latest("date_created")
            if validate_enrollmentSetup(request, sy):
                enb_ob = enrollment_admission_setup.objects.exclude(Q(start_date__gt=date.today()) | Q(
                    end_date__lt=date.today()) | Q(still_accepting=False)).filter(ea_setup_sy=sy)

                if enb_ob:
                    enb_ob1 = enb_ob.first()
                    if enb_ob1.start_date <= date.today() and enb_ob1.end_date >= date.today() and enb_ob1.still_accepting:
                        # If enrollment and admission is ongoing

                        get_user_admission_obj = student_admission_details.objects.filter(
                            admission_owner__id=request.user.id)  # We will use this qs to check user admission

                        if get_user_admission_obj:
                            # If user have admission details submitted
                            get_user_admission_obj_f1 = get_user_admission_obj.first()

                            if get_user_admission_obj_f1.is_validated and not get_user_admission_obj_f1.is_denied:
                                return HttpResponseRedirect(reverse("studentportal:enrollment_application"))
                            else:
                                if get_user_admission_obj_f1.admission_sy == sy:
                                    return HttpResponseRedirect(reverse("studentportal:enrollment_application"))
                                else:
                                    return super().dispatch(request, *args, **kwargs)
                        else:
                            # If the looged-in user have no admission details. The user will redirect to the admission application form
                            return super().dispatch(request, *args, **kwargs)
                    else:
                        return HttpResponseRedirect(reverse("studentportal:index"))
                else:
                    return HttpResponseRedirect(reverse("studentportal:index"))
            else:
                return HttpResponseRedirect(reverse("studentportal:index"))

        except:
            return HttpResponseRedirect(reverse("studentportal:index"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class enrollment_application(FormView):
    form_class = enrollment_form
    template_name = "studentportal/enrollment_HTMLs/enrollment_application_form.html"
    success_url = "/Admission/Admission_details/"

    def form_valid(self, form):
        if not student_contact_number.objects.exclude(contactnum_owner=self.request.user, cellphone_number=form.cleaned_data["contact_number"]).filter(cellphone_number=form.cleaned_data["contact_number"]).exists():
            try:
                student_enrollment_details.objects.create(
                    student_user=self.request.user,
                    admission_details=student_admission_details.objects.get(
                        admission_owner__id=self.request.user.id),
                    selected_strand=shs_strand.objects.get(
                        id=form.cleaned_data["selected_strand"]),
                    full_name=form.cleaned_data["full_name"],

                    home_address=student_address.objects.create(
                        address_owner=self.request.user,
                        permanent_home_address=form.cleaned_data["home_address"],
                    ),

                    age=form.cleaned_data["age"],
                    contact_number=self.validate_cp_num(
                        form.cleaned_data['contact_number']),

                    card=student_report_card.objects.create(
                        report_card_owner=self.request.user,
                        report_card=form.cleaned_data["card"]
                    ),

                    profile_image=student_profile_image.objects.create(
                        image_user=self.request.user,
                        user_image=form.cleaned_data["profile_image"]
                    ),

                    enrolled_schoolyear=school_year.objects.latest(
                        'date_created'),

                )
                messages.success(
                    self.request, "Enrollment is submitted successfully. Kindly wait for the next validation status.")
                return super().form_valid(form)
            except Exception as e:
                messages.error(self.request, e)
                return self.form_invalid(form)
        else:
            messages.warning(self.request, "%s already taken." %
                             form.cleaned_data["contact_number"])
            return self.form_invalid(form)

    def validate_cp_num(self, num):
        get_c = student_contact_number.objects.filter(
            contactnum_owner=self.request.user, cellphone_number=num)
        if get_c:
            return get_c.first()
        else:
            return student_contact_number.objects.create(contactnum_owner=self.request.user, cellphone_number=num)

    def dispatch(self, request, *args, **kwargs):
        try:
            sy = school_year.objects.latest('date_created')
            if validate_enrollmentSetup(request, sy):
                enb_ob = enrollment_admission_setup.objects.exclude(Q(start_date__gt=date.today()) | Q(
                    end_date__lt=date.today()) | Q(still_accepting=False)).filter(ea_setup_sy=sy)

                if enb_ob:
                    enb_ob1 = enb_ob.first()
                    if enb_ob1.start_date <= date.today() and enb_ob1.end_date >= date.today() and enb_ob1.still_accepting:
                        # If enrollment and admission is ongoing
                        get_admission_obj = student_admission_details.objects.filter(
                            admission_owner__id=request.user.id)
                        if get_admission_obj:
                            get_admission_obj_v1 = get_admission_obj.first()
                            if get_admission_obj_v1.is_validated and not get_admission_obj_v1.is_denied:
                                if self.no_existing_enrollment_details(sy):
                                    return super().dispatch(request, *args, **kwargs)
                                messages.warning(
                                    request, "Only one enrollment per school year is valid.")
                                return HttpResponseRedirect(reverse("studentportal:index"))
                            else:
                                if get_admission_obj_v1.admission_sy == sy:
                                    if self.no_existing_enrollment_details(sy):
                                        return super().dispatch(request, *args, **kwargs)
                                    messages.warning(
                                        request, "Only one enrollment per school year is valid.")
                                    return HttpResponseRedirect(reverse("studentportal:index"))
                                else:
                                    messages.warning(
                                        request, "You need to create a new admission before enrollment.")
                                    return HttpResponseRedirect(reverse("studentportal:admission_application"))
                        else:
                            messages.warning(
                                request, "You need to create an admission before enrollment.")
                            return HttpResponseRedirect(reverse("studentportal:admission_application"))
                    else:
                        return HttpResponseRedirect(reverse("studentportal:index"))
                else:
                    return HttpResponseRedirect(reverse("studentportal:index"))
            else:
                return HttpResponseRedirect(reverse("studentportal:index"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("studentportal:index"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Enrollment Application"
        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""
        return context

    def no_existing_enrollment_details(self, sy):
        try:
            get_enrollment = student_enrollment_details.objects.filter(
                student_user=self.request.user, enrolled_schoolyear=sy)
            if get_enrollment:
                return False
            # Return False if the student already have enrollment for the latest school year
            return True
        except Exception as e:
            messages.error(self.request, e)
            return HttpResponseRedirect(reverse("studentportal:index"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class submitted_admission_details(FormView):
    template_name = "studentportal/application_HTMLs/admission_application_details.html"
    form_class = all_admission_forms
    success_url = "/Admission/Admission_details/"

    def form_valid(self, form):
        try:
            if form.has_changed():
                stud_admission_obj = student_admission_details.objects.get(
                    admission_owner=self.request.user)
                if not stud_admission_obj.is_validated and stud_admission_obj.is_denied:
                    count_reviews = for_review_admission.objects.filter(
                        to_review=stud_admission_obj).count()
                    if count_reviews > 0:
                        list_of_fields = form.changed_data
                        for field in list_of_fields:
                            setattr(stud_admission_obj, field,
                                    form.cleaned_data[field])
                        stud_admission_obj.is_validated = False
                        stud_admission_obj.is_denied = False
                        stud_admission_obj.save()
                        messages.success(
                            self.request, "Submitted successfully")
                        return super().form_valid(form)
                    return self.form_invalid(form)
                return self.form_invalid(form)
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        stud_admission_obj = student_admission_details.objects.filter(
            admission_owner=self.request.user)
        if stud_admission_obj:
            stud_admission_obj_f1 = stud_admission_obj.first()
            if (stud_admission_obj_f1.is_validated and not stud_admission_obj_f1.is_denied) or validate_enrollmentSetup(self.request, stud_admission_obj_f1.admission_sy):
                # If admission is validated, if not, then the admission school year must be latest
                initial["first_name"] = stud_admission_obj_f1.first_name
                initial["middle_name"] = stud_admission_obj_f1.middle_name
                initial["last_name"] = stud_admission_obj_f1.last_name
                initial["sex"] = stud_admission_obj_f1.sex
                initial["date_of_birth"] = stud_admission_obj_f1.date_of_birth
                initial["birthplace"] = stud_admission_obj_f1.birthplace
                initial["nationality"] = stud_admission_obj_f1.nationality
                initial["first_chosen_strand"] = stud_admission_obj_f1.first_chosen_strand
                initial["second_chosen_strand"] = stud_admission_obj_f1.second_chosen_strand

                initial["elem_name"] = stud_admission_obj_f1.elem_name
                initial["elem_address"] = stud_admission_obj_f1.elem_address
                initial["elem_region"] = stud_admission_obj_f1.elem_region
                initial["elem_year_completed"] = stud_admission_obj_f1.elem_year_completed
                initial["elem_pept_passer"] = stud_admission_obj_f1.elem_pept_passer
                initial["elem_pept_date_completion"] = stud_admission_obj_f1.elem_pept_date_completion
                initial["elem_ae_passer"] = stud_admission_obj_f1.elem_ae_passer
                initial["elem_ae_date_completion"] = stud_admission_obj_f1.elem_ae_date_completion
                initial["elem_community_learning_center"] = stud_admission_obj_f1.elem_community_learning_center
                initial["elem_clc_address"] = stud_admission_obj_f1.elem_clc_address

                initial["jhs_name"] = stud_admission_obj_f1.jhs_name
                initial["jhs_address"] = stud_admission_obj_f1.jhs_address
                initial["jhs_region"] = stud_admission_obj_f1.jhs_region
                initial["jhs_year_completed"] = stud_admission_obj_f1.jhs_year_completed
                initial["jhs_pept_passer"] = stud_admission_obj_f1.jhs_pept_passer
                initial["jhs_pept_date_completion"] = stud_admission_obj_f1.jhs_pept_date_completion
                initial["jhs_ae_passer"] = stud_admission_obj_f1.jhs_ae_passer
                initial["jhs_ae_date_completion"] = stud_admission_obj_f1.jhs_ae_date_completion
                initial["jhs_community_learning_center"] = stud_admission_obj_f1.jhs_community_learning_center
                initial["jhs_clc_address"] = stud_admission_obj_f1.jhs_clc_address
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Admission Details"

        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""

        try:
            stud_admission_obj = student_admission_details.objects.filter(
                admission_owner=self.request.user)

            if stud_admission_obj:
                stud_admission_obj_f1 = stud_admission_obj.first()

                if stud_admission_obj_f1.is_validated and not stud_admission_obj_f1.is_denied:
                    # If admission is valid
                    context["admission_status"] = "Validated"
                else:
                    if validate_enrollmentSetup(self.request, stud_admission_obj_f1.admission_sy):
                        # If admission is invalid but the admission school year is latest

                        count_reviews = for_review_admission.objects.filter(
                            to_review=stud_admission_obj_f1).count()

                        if not stud_admission_obj_f1.is_validated and stud_admission_obj_f1.is_denied and count_reviews > 0:
                            # If denied with reviews
                            context["admission_status"] = "For revison"
                            context["admission_comments"] = for_review_admission.objects.values_list(
                                'comment', flat=True).filter(to_review=stud_admission_obj_f1).order_by('-date_created')
                        elif not stud_admission_obj_f1.is_validated and stud_admission_obj_f1.is_denied and count_reviews == 0:
                            # If denied with no reviews
                            context["admission_status"] = "Denied"
                        else:
                            context["admission_status"] = self.find_admission_status(
                                stud_admission_obj_f1)
                    else:
                        # If admission is invalid and admission school year is not latest
                        context['invalid_previous_admission'] = True
            else:
                context['no_admission'] = True
                context['admission_status'] = False

        except Exception as e:
            # messages.error(self.request, e)
            pass

        return context

    def find_admission_status(self, obj):
        if not obj.is_validated and not obj.is_denied:
            # If pending
            return "Pending"
        elif obj.is_validated and obj.is_denied:
            return "On-hold"


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class submitted_enrollment_details(FormView):
    form_class = enrollment_form_revision
    template_name = "studentportal/application_HTMLs/enrollment_application_details.html"
    success_url = "/Enrollment/Enrollment_details/"

    def form_valid(self, form):
        # Function for revision
        try:
            if form.has_changed():
                sy = school_year.objects.latest('date_created')
                stud_enrollment_obj = student_enrollment_details.validObjects.select_related(
                    'student_user', 'admission_details', 'selected_strand', 'contact_number', 'card', 'profile_image', 'enrolled_schoolyear').filter(student_user=self.request.user, enrolled_schoolyear=sy)
                if stud_enrollment_obj:
                    obj1 = stud_enrollment_obj.first()
                    count_reviews = enrollment_review.objects.filter(
                        to_review=obj1).count()
                    if count_reviews > 0 and (not obj1.is_passed and obj1.is_denied):
                        # if enrollment is for revision

                        if "contact_number" in form.changed_data:
                            if student_contact_number.objects.exclude(contactnum_owner=self.request.user, cellphone_number=form.cleaned_data["contact_number"]).filter(cellphone_number=form.cleaned_data["contact_number"]).exists():
                                messages.warning(
                                    self.request, "%s is already taken." % form.cleaned_data["contact_number"])
                                return self.form_invalid(form)
                            self.save_update(form, form.changed_data, sy)
                        else:
                            self.save_update(form, form.changed_data, sy)
                        messages.success(
                            self.request, "Enrollment will be validated again.")
                        return super().form_valid(form)

                    return self.form_invalid(form)
                return self.form_invalid(form)
            else:
                return super().form_valid(form)
        except Exception as e:
            # messages.error(self.request, e)
            return self.form_invalid(form)

    def save_update(self, form, changed_fields, sy):
        with transaction.atomic():
            get_update = student_enrollment_details.validObjects.select_related('selected_strand', 'home_address', 'contact_number', 'card', 'profile_image').select_for_update(
                of=('self', 'selected_strand', 'home_address', 'contact_number', 'card', 'profile_image')).get(student_user=self.request.user, enrolled_schoolyear=sy)
            for field in changed_fields:
                if field == "selected_strand":
                    setattr(get_update, field, shs_strand.objects.get(
                        id=int(form.cleaned_data[field])))
                elif field == "home_address":
                    setattr(get_update, field, student_address.objects.create(
                        address_owner=self.request.user, permanent_home_address=form.cleaned_data[field]))
                elif field == "contact_number":
                    setattr(get_update, field, self.validate_cp_num(
                        form.cleaned_data[field]))
                elif field == "card":
                    setattr(get_update, field, student_report_card.objects.create(
                        report_card_owner=self.request.user, report_card=form.cleaned_data["card"]))
                elif field == "profile_image":
                    setattr(get_update, field, student_profile_image.objects.create(
                        image_user=self.request.user, user_image=form.cleaned_data["profile_image"]))
                else:
                    setattr(get_update, field,
                            form.cleaned_data[field])
            get_update.is_passed = False
            get_update.is_denied = False
            get_update.save()

    def validate_cp_num(self, num):
        get_c = student_contact_number.objects.filter(
            contactnum_owner=self.request.user, cellphone_number=num)
        if get_c:
            return get_c.first()
        else:
            return student_contact_number.objects.create(contactnum_owner=self.request.user, cellphone_number=num)

    def get_initial(self):
        initial = super().get_initial()

        if "pk" in self.kwargs:
            get_enrollment = student_enrollment_details.objects.select_related(
                'selected_strand', 'home_address', 'contact_number', 'card', 'profile_image').get(id=self.kwargs["pk"])
        else:
            get_enrollment = student_enrollment_details.objects.select_related(
                'selected_strand', 'home_address', 'contact_number', 'card', 'profile_image').filter(student_user=self.request.user).order_by('-date_created').first()

        if get_enrollment:
            initial["full_name"] = get_enrollment.full_name
            initial["selected_strand"] = get_enrollment.selected_strand.id
            initial["home_address"] = str(get_enrollment.home_address)
            initial["age"] = int(get_enrollment.age)
            initial["contact_number"] = str(get_enrollment.contact_number)

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Enrollment Details"

        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""

        try:
            # Get the list of enrolled sy to display on a button
            context["enrolled_sy"] = student_enrollment_details.objects.values(
                'enrolled_schoolyear__sy', 'id').filter(student_user=self.request.user).order_by('-date_created')

            if "pk" in self.kwargs:
                # If the user enter the enrollment id
                get_imgs = student_enrollment_details.objects.select_related('card', 'profile_image', 'enrolled_schoolyear').filter(
                    student_user=self.request.user, id=int(self.kwargs["pk"])).first()

            elif not "pk" in self.kwargs:
                # When user clicked the enrollment button from the application tab
                # If the user logged-in is enrolled to any school year, and no pk in url

                get_imgs = student_enrollment_details.objects.select_related('card', 'profile_image', 'enrolled_schoolyear').filter(
                    student_user=self.request.user).order_by('-date_created').first()  # Get the latest enrollment of the student

            else:
                pass

            if get_imgs:
                # If user has enrollment
                context["card_url"] = get_imgs.card
                context["photo_url"] = get_imgs.profile_image

                if validate_enrollmentSetup(self.request, get_imgs.enrolled_schoolyear):
                    # To display the enrollment status and follow-up or submit buttons.
                    # If the enrollment_sy is valid, the status and a designated buttons will be displayed.
                    count_review = enrollment_review.objects.filter(
                        to_review=get_imgs).count()
                    if count_review > 0 and (not get_imgs.is_passed and get_imgs.is_denied):
                        # If enrollment status is denied and up for revision
                        context["enrollment_status"] = "For revision"
                        context['enrollment_reviews'] = enrollment_review.objects.values_list(
                            'comment', flat=True).filter(to_review=get_imgs).order_by('-date_created')
                    elif count_review == 0 and (not get_imgs.is_passed and get_imgs.is_denied):
                        # If enrollment is denied

                        # To display the follow-up button
                        context['is_denied'] = True
                        context['enrollment_status'] = "Denied"
                    else:
                        context['enrollment_status'] = self.enrollment_status(
                            get_imgs)
                else:
                    # To display the status only, if the enrollment_sy is no longer valid
                    context['enrollment_status'] = self.enrollment_status(
                        get_imgs)
            else:
                context['no_enrollment'] = True

        except Exception as e:
            # messages.error(self.request, e)
            context["no_enrollment"] = True
        return context

    def enrollment_status(self, enrollment):
        if enrollment.is_passed and enrollment.is_denied:
            return "Hold"
        elif not enrollment.is_passed and enrollment.is_denied:
            return "Denied"
        elif enrollment.is_passed and not enrollment.is_denied:
            return "Validated"
        elif not enrollment.is_passed and not enrollment.is_denied:
            return "Pending"
        else:
            return "No longer valid!"

    def dispatch(self, request, *args, **kwargs):
        try:
            if "pk" in self.kwargs:
                if student_enrollment_details.objects.filter(student_user=request.user, id=self.kwargs["pk"]).exists():
                    return super().dispatch(request, *args, **kwargs)
                return HttpResponseRedirect(reverse("studentportal:enrollment_details"))
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            # messages.error(request, e)
            return HttpResponseRedirect(reverse("studentportal:index"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class view_myDocumentRequest(TemplateView):
    template_name = "studentportal/documentRequests/requestedDocuments.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Requested Documents"

        context["requestedDocuments"] = documentRequest.objects.annotate(
            can_resched=Case(
                When(scheduled_date__gte=date.today(), then=Value(True)),
                default=Value(False),
            ),
            is_cancelled=Case(
                When(is_cancelledByRegistrar=True, then=Value(True)),
                default=Value(False),
            )
        ).filter(request_by=self.request.user).only("document", "scheduled_date")

        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class create_documentRequest(FormView):
    template_name = "studentportal/documentRequests/makeDocumentRequest.html"
    form_class = makeDocumentRequestForm
    success_url = "/DocumentRequests/"

    def form_valid(self, form):
        try:
            checkDocu = documentRequest.objects.filter(document__id=int(
                form.cleaned_data["documents"]), scheduled_date__gte=date.today()).first()
            if checkDocu:
                messages.warning(
                    self.request, f"You have an upcoming schedule to claim your {checkDocu.document.documentName} on {(checkDocu.scheduled_date).strftime('%A, %B %d, %Y')}.")
                return self.form_invalid(form)
            documentRequest.objects.create(
                document=studentDocument.objects.get(
                    pk=int(form.cleaned_data["documents"])),
                request_by=self.request.user,
                scheduled_date=form.cleaned_data["scheduled_date"]
            )
            # email_requestDocument(self.request, self.request.user, {"type": form.cleaned_data["documents"], "schedule": (
            #     form.cleaned_data["scheduled_date"]).strftime("%A, %B %d, %Y")})
            messages.success(self.request, "Document request is sent.")
            return super().form_valid(form)

        except IntegrityError:
            messages.error(
                self.request, "Invalid to request same document at the same time.")
            return self.form_invalid(form)

        except Exception as e:
            messages.error(self.request, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Request a Document"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class reschedDocumentRequest(FormView):
    template_name = "studentportal/documentRequests/reschedRequest.html"
    form_class = makeDocumentRequestForm
    success_url = "/DocumentRequests/"

    def get_initial(self):
        initial = super().get_initial()
        initial["documents"] = self.obj.document.documentName
        initial["scheduled_date"] = self.obj.scheduled_date
        return initial

    def form_valid(self, form):
        if form.has_changed():
            with transaction.atomic():
                update_request = documentRequest.objects.select_for_update().get(pk=self.obj.id)
                update_request.scheduled_date = form.cleaned_data["scheduled_date"]
                if update_request.is_cancelledByRegistrar:
                    update_request.is_cancelledByRegistrar = False
                update_request.save()

            # email_requestDocument(self.request, self.request.user, {"type": form.cleaned_data["documents"], "schedule": (
            #     form.cleaned_data["scheduled_date"]).strftime("%A, %B %d, %Y")})
            return super().form_valid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Reschedule of Request"
        return context

    def dispatch(self, request, *args, **kwargs):
        self.obj = documentRequest.objects.filter(
            pk=int(self.kwargs["pk"]), scheduled_date__gte=date.today()).first()
        if self.obj:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseRedirect(reverse("studentportal:view_myDocumentRequest"))
