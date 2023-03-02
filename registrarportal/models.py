from django.db import models, transaction
from datetime import date
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


def add_school_year(start_year, year):
    try:
        return start_year.replace(year=start_year.year + year)
    except ValueError:
        return start_year.replace(year=start_year.year + year, day=28)


class schoolYear(models.Model):
    start_on = models.DateField()
    until = models.DateField()
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return " ".join(map(str, [self.start_on.strftime("%Y"), "-", (add_school_year(self.start_on, 1)).strftime("%Y")]))

    def display_sy(self):
        return " ".join(map(str, [self.start_on.strftime("%Y"), "-", (add_school_year(self.start_on, 1)).strftime("%Y")]))


class enrollment_admission_setup(models.Model):
    ea_setup_sy = models.OneToOneField(
        schoolYear, on_delete=models.RESTRICT, related_name="e_a_setup")
    start_date = models.DateField()
    end_date = models.DateField()
    students_perBatch = models.IntegerField()
    acceptResponses = models.BooleanField(default=True)
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.ea_setup_sy.display_sy()}: {self.start_date} - {self.end_date}"


class student_admission_details(models.Model):

    class applicant_type(models.TextChoices):
        PINOY = '1', _('Philippine Born')
        FOREIGN_CITIZEN = '2', _('Foreign Citizen')
        DUAL_CITIZEN = '3', _('Dual Citizen')

    class SexChoices(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')

    admission_owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="admission_details")
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

    is_accepted = models.BooleanField(default=False)  # if pending or accepted
    admission_sy = models.ForeignKey(
        schoolYear, on_delete=models.RESTRICT, related_name="sy_admitted")
    first_chosen_strand = models.ForeignKey(
        "adminportal.shs_strand", on_delete=models.RESTRICT, related_name="first_strand")
    second_chosen_strand = models.ForeignKey(
        "adminportal.shs_strand", on_delete=models.RESTRICT, related_name="second_strand")
    assigned_curriculum = models.ForeignKey(
        "adminportal.curriculum", on_delete=models.RESTRICT, related_name="with_admission")
    type = models.CharField(max_length=1, choices=applicant_type.choices)

    is_denied = models.BooleanField(default=False)  # if denied, for review
    with_enrollment = models.BooleanField(default=False)
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-admission_sy__id", "created_on"]
        get_latest_by = ["created_on"]

    def __str__(self):
        return f"{self.id}: {self.first_name} {self.middle_name} {self.last_name}"

    def elementary_school(self):
        return self.elem_name

    def jhs(self):
        return self.jhs_name

    @classmethod
    def admit_this_students(cls, iDs):
        for id in iDs:
            with transaction.atomic():
                obj = cls.objects.select_for_update().get(id=id)
                obj.is_accepted = True
                if obj.is_denied:
                    obj.is_denied = False
                obj.save()

    # def to_pendingList(self):
    #     return reverse("adminportal:admission")

    # def to_admittedList(self):
    #     return reverse("adminportal:admitted_students")

    # def to_reviewList(self):
    #     return reverse("adminportal:forReviewAdmission")

    # def to_deniedList(self):
    #     return reverse("adminportal:denied_admissions")

    # def to_holdList(self):
    #     return reverse("adminportal:hold_admissions")


class admission_requirements(models.Model):
    good_moral = models.ImageField(upload_to="admission/goodMorals/%Y")
    report_card = models.ImageField(upload_to="admission/reportCards/%Y")
    psa = models.ImageField(upload_to="admission/studentPsa/%Y")

    class Meta:
        abstract = True


class ph_born(admission_requirements):
    admission = models.ForeignKey(
        student_admission_details, on_delete=models.RESTRICT, related_name="softCopy_admissionRequirements_phBorn")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id)


class foreign_citizen_documents(admission_requirements):
    admission = models.ForeignKey(
        student_admission_details, on_delete=models.RESTRICT, related_name="softCopy_admissionRequirements_foreigner")
    alien_certificate_of_registration = models.ImageField(
        upload_to="admission/foreignCitizenDocuments/alienRegistration/%Y")
    study_permit = models.ImageField(
        upload_to="admission/foreignCitizenDocuments/studyPermit/%Y")
    f137 = models.ImageField(
        upload_to="admission/foreignCitizenDocuments/f137s/%Y")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id)


class dual_citizen_documents(admission_requirements):
    admission = models.ForeignKey(
        student_admission_details, on_delete=models.RESTRICT, related_name="softCopy_admissionRequirements_dualCitizen")
    dual_citizenship = models.ImageField(
        upload_to="admission/dualCitizenDocuments/dualCitizenshipCertificates/%Y")
    philippine_passport = models.ImageField(
        upload_to="admission/dualCitizenDocuments/phPassports/%Y")
    f137 = models.ImageField(
        upload_to="admission/dualCitizenDocuments/f137s/%Y")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id)


class admisssion_batch_manager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(sy__until__gte=date.today())


class admission_batch(models.Model):
    sy = models.ForeignKey(
        schoolYear, on_delete=models.RESTRICT, related_name="sy_admission_batches")
    members = models.ManyToManyField(
        student_admission_details, related_name="admission_batch_member")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    new_batches = admisssion_batch_manager()

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id)


class enrollment_manager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_accepted=True, is_denied=False)


class student_enrollment_details(models.Model):
    class year_levels(models.TextChoices):
        grade_11 = '11', _('Grade 11')
        grade_12 = '12', _('Grade 12')

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="stud_enrollment")
    admission = models.ForeignKey(
        student_admission_details, on_delete=models.RESTRICT, related_name="enrollment")
    strand = models.ForeignKey(
        "adminportal.shs_strand", on_delete=models.RESTRICT, related_name="strand_enrollment")
    year_level = models.CharField(max_length=7, choices=year_levels.choices)
    full_name = models.CharField(max_length=120)
    age = models.IntegerField()
    is_accepted = models.BooleanField(default=False)
    is_denied = models.BooleanField(default=False)
    enrolled_school_year = models.ForeignKey(
        schoolYear, on_delete=models.RESTRICT, related_name="sy_enrollee")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    validatedObjects = enrollment_manager()

    def __str__(self):
        return self.id

    class Meta:
        ordering = ["-enrolled_school_year__id", "created_on"]
        unique_together = ["applicant", "admission", "enrolled_school_year"]


class student_home_address(models.Model):
    home_of = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="user_address")
    permanent_home_address = models.CharField(max_length=50)
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.permanent_home_address

    class Meta:
        ordering = ["-created_on"]


class student_contact_number(models.Model):
    own_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="user_contact")
    cp_number_regex = RegexValidator(regex=r"^(09)([0-9]{9})$")
    cellphone_number = models.CharField(
        max_length=11, unique=True, validators=[cp_number_regex])
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cellphone_number

    class Meta:
        ordering = ["-created_on"]


class student_report_card(models.Model):
    card_from = models.ForeignKey(
        student_enrollment_details, on_delete=models.RESTRICT, related_name="report_card")
    report_card = models.ImageField(upload_to="enrollment/report_cards/%Y")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id

    class Meta:
        ordering = ["-created_on"]


class student_id_picture(models.Model):
    image_from = models.ForeignKey(
        student_enrollment_details, on_delete=models.RESTRICT, related_name="stud_pict")
    user_image = models.ImageField(upload_to="enrollment/user_pic/%Y")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id

    class Meta:
        ordering = ["-created_on"]


class enrollment_batch_manager(models.Model):
    def get_queryset(self):
        return super().get_queryset().filter(sy__until__gte=date.today())


class enrollment_batch(models.Model):
    sy = models.ForeignKey(
        schoolYear, on_delete=models.RESTRICT, related_name="sy_enrollment_batches")
    section = models.ForeignKey("adminportal.schoolSections",
                                on_delete=models.RESTRICT, related_name="section_batch")
    members = models.ManyToManyField(
        student_enrollment_details, related_name="enrollment_batch_member")
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    new_batches = enrollment_batch_manager()

    class Meta:
        ordering = ["created_on"]

    def __str__(self):
        return str(self.id)
