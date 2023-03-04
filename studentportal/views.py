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
from adminportal.models import *
from collections import OrderedDict
from django.core.files.storage import DefaultStorage
from registrarportal.models import student_admission_details
import cv2
import pytesseract
from PIL import Image
from registrarportal.tokenGenerators import generate_enrollment_token, new_enrollment_token_for_old_students
from usersPortal.models import user_profile
from django.core.exceptions import ObjectDoesNotExist


# pytesseract.pytesseract.tesseract_cmd = 'C:\\Users\\Administrator\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
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

        getEvents = school_events.ongoingEvents.all()
        if getEvents:
            dct = dict()
            for event in getEvents:
                if event.start_on.strftime("%B") not in dct:
                    dct[event.start_on.strftime("%B")] = list()
                    dct[event.start_on.strftime("%B")].append(event)
                else:
                    dct[event.start_on.strftime("%B")].append(event)
            context["events"] = dct

        context["user_profilePicture"] = load_userPic(
            self.request.user) if self.request.user.is_authenticated else ""

        return context


def user_no_admission(user):
    # Return False if the user has validated admission or to_validate admission
    return not student_admission_details.objects.filter(admission_owner=user).exclude(is_denied=True).exists()


def check_for_admission_availability(user):
    return enrollment_admission_setup.objects.filter(ea_setup_sy__until__gt=date.today(), end_date__gte=date.today()).exists()


admission_decorators = [login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index"), user_passes_test(
    user_no_admission, login_url="studentportal:index"), user_passes_test(check_for_admission_availability, login_url="studentportal:index")]


@method_decorator(admission_decorators, name="dispatch")
class select_admission_type(TemplateView):
    template_name = "studentportal/admissionForms/chooseAdmissionType.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Type of Applicant"
        context["types"] = student_admission_details.applicant_type.choices
        return context

    def dispatch(self, request, *args, **kwargs):
        self.get_latest = enrollment_admission_setup.objects.filter(
            ea_setup_sy__until__gt=date.today(), end_date__gte=date.today()).first()
        if self.get_latest and self.get_latest.acceptResponses:
            return super().dispatch(request, *args, **kwargs)

        messages.warning(
            request, "We no longer accept responses for the admission. Please wait for further announcement.")
        return HttpResponseRedirect(reverse("studentportal:index"))


@method_decorator(admission_decorators, name="dispatch")
class admission(SessionWizardView):
    templates = {
        "admission_personal_details": "studentportal/admissionForms/studentDetailsForm.html",
        "elementary_school_details": "studentportal/admissionForms/addPrimarySchoolForm.html",
        "jhs_details": "studentportal/admissionForms/addJHSForm.html",
        "admissionRequirementsForm": "studentportal/admissionForms/phBornDocumentForm.html",
        "foreignApplicantForm": "studentportal/admissionForms/foreignApplicantDocumentForm.html",
        "dualCitizenApplicantForm": "studentportal/admissionForms/dualCitizenApplicantDocumentForm.html",
        "dummy_form": "studentportal/admissionForms/dummyForm.html",
    }

    form_list = [
        ("admission_personal_details", admission_personal_details),
        ("elementary_school_details", elementary_school_details),
        ("jhs_details", jhs_details),
        ("admissionRequirementsForm", admissionRequirementsForm),
        ("foreignApplicantForm", foreignApplicantForm),
        ("dualCitizenApplicantForm", dualCitizenApplicantForm),
        ("dummy_form", dummy_form),
    ]

    file_storage = DefaultStorage()

    def get_form_list(self):
        form_list = OrderedDict()

        form_list["admission_personal_details"] = admission_personal_details
        form_list["elementary_school_details"] = elementary_school_details
        form_list["jhs_details"] = jhs_details

        if self.kwargs["pk"] == "1":
            form_list["admissionRequirementsForm"] = admissionRequirementsForm
        elif self.kwargs["pk"] == "2":
            form_list["foreignApplicantForm"] = foreignApplicantForm
        else:
            form_list["dualCitizenApplicantForm"] = dualCitizenApplicantForm

        form_list["dummy_form"] = dummy_form

        return form_list

    def initialize_row(self, myDict):
        for key, value in myDict.items():
            match key:
                case ("first_chosen_strand" | "second_chosen_strand"):
                    setattr(self.get_admission, key,
                            shs_strand.objects.get(id=int(value)))
                case "elem_pept_date_completion":
                    setattr(self.get_admission, key,
                            value if myDict["elem_pept_passer"] else None)
                case "elem_ae_date_completion":
                    setattr(self.get_admission, key,
                            value if myDict["elem_ae_passer"] else None)
                case "jhs_pept_date_completion":
                    setattr(self.get_admission, key,
                            value if myDict["jhs_pept_passer"] else None)
                case "jhs_ae_date_completion":
                    setattr(self.get_admission, key,
                            value if myDict["jhs_ae_passer"] else None)
                case _:
                    setattr(self.get_admission, key, value)

    def initialize_foreignTables(self, myDict):
        for key, value in myDict.items():
            setattr(self.init_docu, key, value)

    def done(self, form_list, **kwargs):
        try:
            personalDetails = self.get_cleaned_data_for_step(
                "admission_personal_details")
            primarySchoolDetails = self.get_cleaned_data_for_step(
                "elementary_school_details")
            secondarySchoolDetails = self.get_cleaned_data_for_step(
                "jhs_details")
            documents = ""

            if kwargs["pk"] == "1":
                documents = self.get_cleaned_data_for_step(
                    "admissionRequirementsForm")
                self.init_docu = ph_born()
            elif kwargs["pk"] == "2":
                documents = self.get_cleaned_data_for_step(
                    "foreignApplicantForm")
                self.init_docu = foreign_citizen_documents()
            else:
                documents = self.get_cleaned_data_for_step(
                    "dualCitizenApplicantForm")
                self.init_docu = dual_citizen_documents()

            self.get_admission = student_admission_details.objects.filter(
                admission_owner=self.request.user).first()
            if not self.get_admission:
                self.get_admission = student_admission_details()

            self.get_admission.admission_owner = self.request.user
            self.get_admission.is_accepted = False
            self.get_admission.is_denied = False
            self.get_admission.type = int(kwargs["pk"])
            self.get_admission.admission_sy = schoolYear.objects.filter(
                until__gt=date.today()).first()
            self.get_admission.assigned_curriculum = curriculum.objects.filter(
                strand__id=int(personalDetails["first_chosen_strand"])).first()
            self.initialize_row(personalDetails)
            self.initialize_row(primarySchoolDetails)
            self.initialize_row(secondarySchoolDetails)
            self.get_admission.save()

            self.init_docu.admission = self.get_admission
            self.initialize_foreignTables(documents)
            self.init_docu.save()

            messages.success(
                self.request, "Admission saved. Kindly wait for the registrar to validate your request.")

        except Exception as e:
            messages.error(self.request, e)

        return HttpResponseRedirect(reverse("studentportal:index"))

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    # def rescale_frame(self, frame, scale=0.25):
    #     width = int(frame.shape[1] * scale)
    #     height = int(frame.shape[0] * scale)
    #     dimension = (width, height)
    #     return cv2.resize(frame, dimension, interpolation=cv2.INTER_AREA)

    # def render_next_step(self, form, **kwargs):
    #     get_reqs = self.get_cleaned_data_for_step(self.storage.current_step)
    #     t_methods = [cv2.TM_CCOEFF, cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR,
    #                  cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]

    #     if self.storage.current_step == "admissionRequirementsForm":
    #         with Image.open(get_reqs["good_moral"]) as goodMoral:
    #             depedSeal = cv2.imread("Media/Seals/DepedSeal.png")
    #             testSeal = cv2.imread("Media/Seals/sampleSeals.jpg")
    #             depedSeal_h, depedSeal_w, _ = depedSeal.shape
    #         # with Image.open(get_imgs["good_moral"]) as img:
    #         #     txt = pytesseract.image_to_string(img)

    #         result = cv2.matchTemplate(
    #             testSeal, self.rescale_frame(depedSeal), cv2.TM_CCOEFF)
    #         min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    #         messages.success(self.request, (min_loc, max_loc))

    #         return self.render_goto_step(self.storage.current_step, **kwargs)
    #     else:
    #         next_step = self.steps.next
    #         new_form = self.get_form(
    #             next_step,
    #             data=self.storage.get_step_data(next_step),
    #             files=self.storage.get_step_files(next_step),
    #         )
    #         # change the stored current step
    #         self.storage.current_step = next_step
    #         return self.render(new_form, **kwargs)

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
        context["title"] = "Admission"
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            self.get_latest = enrollment_admission_setup.objects.filter(
                ea_setup_sy__until__gt=date.today(), end_date__gte=date.today()).first()
            if self.get_latest and self.get_latest.acceptResponses and kwargs["pk"] in student_admission_details.applicant_type.values:
                return super().dispatch(request, *args, **kwargs)
            else:
                return HttpResponseRedirect(reverse("studentportal:select_type"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("studentportal:select_type"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class view_myDocumentRequest(TemplateView):
    template_name = "studentportal/documentRequests/requestedDocuments.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Requested Documents"

        ongoing_requests = documentRequest.objects.annotate(
            can_resched=Case(
                When(scheduled_date__gte=date.today(), then=Value(True)),
                default=Value(False),
            ),
            is_cancelled=Case(
                When(is_cancelledByRegistrar=True, then=Value(True)),
                default=Value(False),
            )
        ).filter(request_by=self.request.user, scheduled_date__gte=date.today()).only("document", "scheduled_date")

        previous_requests = documentRequest.objects.annotate(can_resched=Case(default=Value(False)), is_cancelled=Case(
            default=Value(False))).filter(request_by=self.request.user, scheduled_date__lt=date.today()).only("document", "scheduled_date")

        context["requestedDocuments"] = ongoing_requests.union(
            previous_requests, all=True)

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


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class enrollment_new_admission(FormView):
    template_name = "studentportal/enrollmentForms/enrollment.html"
    form_class = enrollment_form1
    success_url = "/"

    def form_valid(self, form):
        try:
            get_age = user_profile.objects.get(user=self.request.user)
            if get_age.user_age():
                save_this = student_enrollment_details()
                save_this.applicant = self.request.user
                save_this.admission = student_admission_details.objects.get(
                    admission_owner=self.request.user)
                save_this.strand = shs_strand.objects.get(
                    id=int(form.cleaned_data["select_strand"]))
                save_this.full_name = form.cleaned_data["full_name"]

                save_this.age = get_age.user_age()
                save_this.enrolled_school_year = schoolYear.objects.first()
                save_this.year_level = form.cleaned_data["year_level"]
                save_this.save()

                student_home_address.objects.create(
                    home_of=self.request.user, permanent_home_address=form.cleaned_data["home_address"])
                student_contact_number.objects.create(
                    own_by=self.request.user, cellphone_number=form.cleaned_data["contact_number"])
                student_report_card.objects.create(
                    card_from=save_this, report_card=form.cleaned_data["card"])
                student_id_picture.objects.create(
                    image_from=save_this, user_image=form.cleaned_data["profile_image"])

                adm = student_admission_details.objects.get(
                    admission_owner=self.request.user)
                adm.with_enrollment = True
                adm.save()

                messages.success(
                    self.request, "We received your enrollment. Please wait us to validate it.")
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Enrollment Failed. Please complete your profile to continue.")
                return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, "Enrollment Failed. Nakapag-apply kana this school year.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Enrollment"
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
            admObj = student_admission_details.objects.get(
                pk=uid, admission_owner=request.user)
        except(TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            admObj = None

        if admObj is not None and generate_enrollment_token.check_token(admObj, self.kwargs['token']):
            # Return true if token is still valid
            return super().dispatch(request, *args, **kwargs)
        else:
            # if there's no user found, or the token is no longer valid, or both.
            messages.error(request, "Enrollment link is no longer valid!")
            return HttpResponseRedirect(reverse("studentportal:index"))


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class enrollment_old_students(FormView):
    template_name = "studentportal/enrollmentForms/oldStudent_form.html"
    form_class = enrollment_form2
    success_url = "/"

    def form_valid(self, form):
        try:
            get_age = user_profile.objects.get(user=self.request.user)
            if get_age.user_age():
                save_this = student_enrollment_details()
                save_this.applicant = self.request.user
                save_this.admission = student_admission_details.objects.get(
                    admission_owner=self.request.user)
                save_this.strand = shs_strand.objects.get(
                    id=int(form.cleaned_data["select_strand"]))
                save_this.full_name = form.cleaned_data["full_name"]

                save_this.age = get_age.user_age()
                save_this.enrolled_school_year = schoolYear.objects.first()
                save_this.year_level = '12'
                save_this.save()

                student_home_address.objects.create(
                    home_of=self.request.user, permanent_home_address=form.cleaned_data["home_address"])
                student_contact_number.objects.create(
                    own_by=self.request.user, cellphone_number=form.cleaned_data["contact_number"])
                student_report_card.objects.create(
                    card_from=save_this, report_card=form.cleaned_data["card"])
                student_id_picture.objects.create(
                    image_from=save_this, user_image=form.cleaned_data["profile_image"])

                self.admObj.is_accepted = True
                self.admObj.save()

                messages.success(
                    self.request, "We received your enrollment. Please wait us to validate it.")
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Enrollment Failed. Please complete your profile to continue.")
                return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, "Enrollment Failed. Nakapag-apply kana this school year.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Enrollment"
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
            self.admObj = enrollment_invitations.objects.get(
                pk=uid, invitation_to__admission_owner=request.user)
        except(TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            self.admObj = None

        if self.admObj is not None and new_enrollment_token_for_old_students.check_token(self.admObj, self.kwargs['token']):
            # Return true if token is still valid
            return super().dispatch(request, *args, **kwargs)
        else:
            # if there's no user found, or the token is no longer valid, or both.
            messages.error(request, "Enrollment link is no longer valid!")
            return HttpResponseRedirect(reverse("studentportal:index"))
