from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from datetime import date
from django.core.validators import RegexValidator
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db.models import Q
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse

User = get_user_model()


def split_this_contactnum(cnum):
    # convert this int type into an str object
    cnum = str(cnum)

    # Initialize a list
    this_list = []

    # Iterate each str into list of str
    for obj in cnum:
        this_list.append(obj)

    # Remove 6 3 from the list
    this_list.pop(0)
    this_list.pop(0)

    # initialize new str variable
    new_doc_contact_num = ""

    # iterate each list item and append to str variable
    for each_lst in this_list:
        new_doc_contact_num += each_lst

    # convert str into int
    new_doc_contact_num = int(new_doc_contact_num)

    # return the update contact num to be display back to caller
    return new_doc_contact_num


def current_school_year():
    date_now = date.today()
    years = 1
    try:
        year_only = date_now.replace(year=date_now.year + years)
    except ValueError:
        year_only = date_now.replace(year=date_now.year + years, day=28)
    sy = " ".join(
        map(str, [date_now.strftime("%Y"), "-", year_only.strftime("%Y")]))

    return sy


class school_year(models.Model):
    sy = models.CharField(max_length=11, unique=True)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sy


class shs_track(models.Model):
    track_name = models.CharField(max_length=50, unique=True)
    definition = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.track_name


class shs_strand(models.Model):
    track = models.ForeignKey(
        "shs_track", on_delete=models.PROTECT, related_name="track_strand")
    strand_name = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.strand_name

    def serialize1(self):
        return {
            "track": self.track.track_name,
            "strand_name": self.strand_name,
            "definition": self.definition,
            "date_added": self.date_added,
            "date_modified": self.date_modified,
            "is_deleted": self.is_deleted,
        }


class student_address(models.Model):
    address_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_address")
    permanent_home_address = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.permanent_home_address


class student_contact_number(models.Model):
    contactnum_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_contact")
    cp_number_regex = RegexValidator(regex=r"^(09)([0-9]{9})$")
    cellphone_number = models.CharField(
        max_length=11, unique=True, validators=[cp_number_regex])
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cellphone_number


class student_report_card(models.Model):
    report_card_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_reportcard")
    report_card = models.ImageField(upload_to="Report_cards/%Y/")
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.report_card.url


class student_profile_image(models.Model):
    image_user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_image")
    user_image = models.ImageField(upload_to="User_profiles/")
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_image.url


class student_admission_details(models.Model):

    class SexChoices(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')

    admission_owner = models.OneToOneField(
        User, on_delete=models.PROTECT, related_name="admission_details")
    first_name = models.CharField(max_length=20)
    middle_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    sex = models.CharField(max_length=2, choices=SexChoices.choices)
    date_of_birth = models.DateField()
    birthplace = models.CharField(max_length=200)
    nationality = models.CharField(max_length=50)

    # Elementary school details
    elem_name = models.CharField(max_length=50)
    elem_address = models.CharField(max_length=50)
    elem_region = models.CharField(max_length=30)
    elem_year_completed = models.DateField()
    elem_pept_passer = models.BooleanField(default=False)
    elem_pept_date_completion = models.DateField(null=True, blank=True)
    elem_ae_passer = models.BooleanField(default=False)
    elem_ae_date_completion = models.DateField(null=True, blank=True)
    elem_community_learning_center = models.CharField(
        max_length=50, null=True, blank=True)
    elem_clc_address = models.CharField(max_length=50, null=True, blank=True)

    # Junior High school details
    jhs_name = models.CharField(max_length=50)
    jhs_address = models.CharField(max_length=50)
    jhs_region = models.CharField(max_length=30)
    jhs_year_completed = models.DateField()
    jhs_pept_passer = models.BooleanField(default=False)
    jhs_pept_date_completion = models.DateField(null=True, blank=True)
    jhs_ae_passer = models.BooleanField(default=False)
    jhs_ae_date_completion = models.DateField(null=True, blank=True)
    jhs_community_learning_center = models.CharField(
        max_length=50, null=True, blank=True)
    jhs_clc_address = models.CharField(max_length=50, null=True, blank=True)

    is_validated = models.BooleanField(default=False)  # if pending or accepted
    admission_sy = models.ForeignKey(
        school_year, on_delete=models.PROTECT, related_name="sy_admitted")
    first_chosen_strand = models.ForeignKey(
        shs_strand, on_delete=models.PROTECT, related_name="first_strand")
    second_chosen_strand = models.ForeignKey(
        shs_strand, on_delete=models.PROTECT, related_name="second_strand")

    is_late = models.BooleanField(default=False)
    is_transferee = models.BooleanField(default=False)

    is_denied = models.BooleanField(default=False)  # if denied, for review
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date_created"]
        get_latest_by = ["date_created"]

    def __str__(self):
        return f"{self.admission_owner}: {self.last_name}, {self.first_name} {self.middle_name} - {self.sex}"

    def elementary_school(self):
        return self.elem_name

    def jhs(self):
        return self.jhs_name

    def student_basic_details(self):
        return {
            "student_acc_id": self.admission_owner.id,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "sex": self.sex,
            "date_of_birth": self.date_of_birth,
            "birthplace": self.birthplace,
            "nationality": self.nationality,
        }

    def to_pendingList(self):
        return reverse("adminportal:admission")

    def to_admittedList(self):
        return reverse("adminportal:admitted_students")

    def to_reviewList(self):
        return reverse("adminportal:forReviewAdmission")

    def to_deniedList(self):
        return reverse("adminportal:denied_admissions")

    def to_holdList(self):
        return reverse("adminportal:hold_admissions")


class studentEnrollment_manager(models.Manager):
    # Use this manager to get enrollments with validated admission
    def get_queryset(self):
        return super().get_queryset().filter(admission_details__is_validated=True, admission_details__is_denied=False)


class student_enrollment_details(models.Model):
    student_user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_enrollment_details")
    admission_details = models.ForeignKey(
        student_admission_details, on_delete=models.PROTECT, related_name="user_student_enrollment_details")
    selected_strand = models.ForeignKey(
        shs_strand, on_delete=models.PROTECT, related_name="chosen_strand")
    full_name = models.CharField(max_length=60)
    home_address = models.ForeignKey(
        student_address, on_delete=models.PROTECT, related_name="student_address")
    age_validator = RegexValidator(regex=r"([0-9])")
    age = models.CharField(max_length=3, validators=[age_validator])
    contact_number = models.ForeignKey(
        student_contact_number, on_delete=models.PROTECT, related_name="cp_number")

    card = models.ForeignKey(
        student_report_card, on_delete=models.PROTECT, related_name="enrollment_report_card")
    profile_image = models.ForeignKey(
        student_profile_image, on_delete=models.PROTECT, related_name="enrollment_profile_image")

    is_passed = models.BooleanField(default=False)
    is_denied = models.BooleanField(default=False)

    is_late = models.BooleanField(default=False)
    is_repeater = models.BooleanField(default=False)

    enrolled_schoolyear = models.ForeignKey(
        school_year, on_delete=models.PROTECT, related_name="sy_enrolled")

    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()  # Default manager
    validObjects = studentEnrollment_manager()

    def __str__(self):
        return self.full_name


class enrollment_admission_setup(models.Model):
    ea_setup_sy = models.OneToOneField(
        school_year, on_delete=models.PROTECT, related_name="setup_sy")
    start_date = models.DateField()
    end_date = models.DateField()
    still_accepting = models.BooleanField(default=True)

    def __str__(self):
        return self.ea_setup_sy.sy


class for_review_admission(models.Model):
    to_review = models.ForeignKey(
        student_admission_details, on_delete=models.CASCADE, related_name="admission_review")
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.to_review.first_name


class enrollment_review(models.Model):
    to_review = models.ForeignKey(
        student_enrollment_details, on_delete=models.CASCADE, related_name="enrollment_review")
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.to_review.full_name


class school_contact_number(models.Model):
    contactnum_owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="contact_number")
    cp_number_regex = RegexValidator(regex=r"^(09)([0-9]{9})$")
    cellphone_number = models.CharField(
        max_length=11, unique=True, validators=[cp_number_regex])
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.cellphone_number


class school_email(models.Model):
    email_from = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="contact_email")
    email = models.EmailField(max_length=50)
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.email
