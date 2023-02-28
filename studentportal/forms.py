from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from adminportal.models import *
from registrarportal.models import *
# from usersPortal.forms import validate_imageSize

User = get_user_model()


def validate_imageSize(picture):
    if picture.size > 2*1024*1024:
        raise ValidationError(
            "File size is too big. 2mb is the maximum allowed size.")


def validate_email_chars(email):
    regex_email = re.compile(r"""^([a-zA-Z0-9_\.]+)
                            @
                            (gmail)
                            \.
                            (com)$
                            """, re.VERBOSE)
    res = regex_email.fullmatch(email)
    if not res:
        raise ValidationError("Invalid email address. Try again.")


def validate_username(name):
    regex_name = re.compile(r""" ([a-z\s]+) """, re.VERBOSE | re.IGNORECASE)

    res = regex_name.fullmatch(name)

    if not res:
        raise ValidationError(
            "Username must be a plain texts. Spaces are allowed.")


def birthdate_validator(dt):
    if dt >= date.today():
        raise ValidationError("Invalid date.")


def boolean_choices():
    bool_choices = (
        (True, 'Yes'),
        (False, 'No'),
    )
    return bool_choices


def validate_cp_number(number):
    regex = r"^(09)([0-9]{9})$"
    if not re.match(regex, str(number)):
        raise ValidationError("Invalid Contact Number")


def validate_schedule(dt):
    if dt <= date.today():
        raise ValidationError("Invalid Date.")


class admission_personal_details(forms.Form):
    first_name = forms.CharField(
        label="First Name", max_length=20, required=False)
    middle_name = forms.CharField(
        label="Middle Name", max_length=20, required=False)
    last_name = forms.CharField(
        label="Last Name", max_length=20, required=False)
    # sex = forms.ChoiceField(
    #     label="Sex", choices=student_admission_details.SexChoices.choices, required=False)
    date_of_birth = forms.DateField(label="Birthdate", validators=[
        birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    birthplace = forms.CharField(
        label="Place of birth", max_length=200, required=False)
    nationality = forms.CharField(
        label="Nationality", max_length=50, required=False)
    first_chosen_strand = forms.TypedChoiceField(label="Choose First Strand", choices=(
        (strand.strand.id, f"{strand.strand.track.track_name}: {strand.strand.strand_name}") for strand in curriculum.objects.order_by('strand').distinct('strand')), coerce=str, required=False)
    second_chosen_strand = forms.TypedChoiceField(label="Choose Second Strand", choices=(
        (strand.strand.id, f"{strand.strand.track.track_name}: {strand.strand.strand_name}") for strand in curriculum.objects.order_by('strand').distinct('strand')), coerce=str, required=False)


class elementary_school_details(forms.Form):
    elem_name = forms.CharField(
        label="Elementary School Name", max_length=50, required=False)
    elem_address = forms.CharField(
        label="Elementary School Address", max_length=50, required=False)
    elem_region = forms.CharField(
        label="School Region", max_length=30, required=False)
    elem_year_completed = forms.DateField(label="Year Completed", validators=[
                                          birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    elem_pept_passer = forms.ChoiceField(
        label="Are you a passer of Philippine Educational Placement Test (PEPT) for Elementary Level?", choices=boolean_choices(), required=False)
    elem_pept_date_completion = forms.DateField(label="Date Completed", validators=[
                                                birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if PEPT passer")
    elem_ae_passer = forms.ChoiceField(
        label="Are you a passer of Accreditation and Equivalency (A&E) Test for Elementary Level?", choices=boolean_choices(), required=False)
    elem_ae_date_completion = forms.DateField(label="Date Completed", validators=[
                                              birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if A&E passer")
    elem_community_learning_center = forms.CharField(
        label="Name of Community Learning Center", max_length=50, required=False, help_text="If applicable")
    elem_clc_address = forms.CharField(
        label="Community Learning Center Address", max_length=50, required=False, help_text="If applicable")


class jhs_details(forms.Form):
    jhs_name = forms.CharField(
        label="Junior High School Name", max_length=50, required=False)
    jhs_address = forms.CharField(
        label="Junior High School Address", max_length=50, required=False)
    jhs_region = forms.CharField(
        label="School Region", max_length=30, required=False)
    jhs_year_completed = forms.DateField(label="Year Completed", validators=[
        birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    jhs_pept_passer = forms.ChoiceField(
        label="Are you a passer of Philippine Educational Placement Test (PEPT) for JHS Level?", choices=boolean_choices(), required=False)
    jhs_pept_date_completion = forms.DateField(label="Date Completed", validators=[
                                               birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if PEPT passer")
    jhs_ae_passer = forms.ChoiceField(
        label="Are you a passer of Accreditation and Equivalency (A&E) Test for JHS Level?", choices=boolean_choices(), required=False)
    jhs_ae_date_completion = forms.DateField(label="Date Completed", validators=[
                                             birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if A&E passer")
    jhs_community_learning_center = forms.CharField(
        label="Name of Community Learning Center", max_length=50, required=False, help_text="If applicable")
    jhs_clc_address = forms.CharField(
        label="Community Learning Center Address", max_length=50, required=False, help_text="If applicable")


class admissionRequirementsForm(forms.Form):
    good_moral = forms.FileField(label="Good Moral Certificate", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    report_card = forms.FileField(label="Report Card", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    psa = forms.FileField(label="Philippine Birth Certificate", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])


class foreignApplicantForm(admissionRequirementsForm):
    alien_certificate_of_registration = forms.FileField(label="Alien Certificate of Registration", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    study_permit = forms.FileField(label="Study Permit", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    f137 = forms.FileField(label="School Permanent Record (F137)", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])


class dualCitizenApplicantForm(admissionRequirementsForm):
    dual_citizenship = forms.FileField(label="Certificate of Dual Citizenship", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    philippine_passport = forms.FileField(label="Philippine Passport", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])
    f137 = forms.FileField(label="School Permanent Record (F137)", widget=forms.ClearableFileInput(
    ), validators=[validate_imageSize, ])


class dummy_form(forms.Form):
    name = forms.CharField(max_length=20, label="Nothing...", required=False)


class enrollment_form1(forms.Form):
    # Form for g11 and transferees
    full_name = forms.CharField(
        max_length=60, label='Full Name (Surname, First Name, Middle Name)')
    select_strand = forms.TypedChoiceField(label="Select Strand", choices=(
        (strand.strand.id, f"{strand.strand.track.track_name}: {strand.strand.strand_name}") for strand in curriculum.objects.order_by('strand').distinct('strand')), coerce=str, required=False)
    home_address = forms.CharField(
        max_length=50, label='Home address (Current)')
    contact_number = forms.CharField(
        label="Contact Number", widget=forms.NumberInput, validators=[validate_cp_number])
    card = forms.ImageField(
        label="Report card", help_text="Report card from previous year or quarter")
    profile_image = forms.ImageField(
        label="Student Photo", help_text="White background with no filters")


# class all_admission_forms(forms.Form):
#     first_name = forms.CharField(label="First Name", max_length=20)
#     middle_name = forms.CharField(label="Middle Name", max_length=20)
#     last_name = forms.CharField(label="Last Name", max_length=20)
#     sex = forms.ChoiceField(
#         label="Sex", choices=student_admission_details.SexChoices.choices)
#     date_of_birth = forms.DateField(label="Birthdate", validators=[
#                                     birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))
#     birthplace = forms.CharField(label="Place of birth", max_length=200)
#     nationality = forms.CharField(label="Nationality", max_length=50)
#     first_chosen_strand = forms.CharField(
#         label='First Strand', disabled=True, required=False)
#     second_chosen_strand = forms.CharField(
#         label='Second Strand', disabled=True, required=False)

#     elem_name = forms.CharField(label="Elementary School Name", max_length=50)
#     elem_address = forms.CharField(
#         label="Elementary School Address", max_length=50)
#     elem_region = forms.CharField(label="School Region", max_length=30)
#     elem_year_completed = forms.DateField(label="Year Completed", validators=[
#                                           birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))

#     elem_pept_passer = forms.TypedChoiceField(
#         label="Are you a passer of Philippine Educational Placement Test (PEPT) for Elementary Level?", choices=boolean_choices(), coerce=str, required=False)
#     elem_pept_date_completion = forms.DateField(label="Date Completed", validators=[
#                                                 birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if PEPT passer")

#     elem_ae_passer = forms.TypedChoiceField(
#         label="Are you a passer of Accreditation and Equivalency (A&E) Test for Elementary Level?", choices=boolean_choices(), coerce=str, required=False)
#     elem_ae_date_completion = forms.DateField(label="Date Completed", validators=[
#                                               birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if A&E passer")

#     elem_community_learning_center = forms.CharField(
#         label="Name of Community Learning Center", max_length=50, required=False, help_text="If applicable")
#     elem_clc_address = forms.CharField(
#         label="Community Learning Center Address", max_length=50, required=False, help_text="If applicable")

#     jhs_name = forms.CharField(label="Junior High School Name", max_length=50)
#     jhs_address = forms.CharField(
#         label="Junior High School Address", max_length=50)
#     jhs_region = forms.CharField(label="School Region", max_length=30)
#     jhs_year_completed = forms.DateField(label="Year Completed", validators=[
#         birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))

#     jhs_pept_passer = forms.TypedChoiceField(
#         label="Are you a passer of Philippine Educational Placement Test (PEPT) for JHS Level?", choices=boolean_choices(), coerce=str, required=False)
#     jhs_pept_date_completion = forms.DateField(label="Date Completed", validators=[
#                                                birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if PEPT passer")

#     jhs_ae_passer = forms.TypedChoiceField(
#         label="Are you a passer of Accreditation and Equivalency (A&E) Test for JHS Level?", choices=boolean_choices(), coerce=str, required=False)
#     jhs_ae_date_completion = forms.DateField(label="Date Completed", validators=[
#                                              birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}), required=False, help_text="Enter date completion if A&E passer")

#     jhs_community_learning_center = forms.CharField(
#         label="Name of Community Learning Center", max_length=50, required=False, help_text="If applicable")
#     jhs_clc_address = forms.CharField(
#         label="Community Learning Center Address", max_length=50, required=False, help_text="If applicable")


# class enrollment_form_revision(forms.Form):
#     full_name = forms.CharField(
#         max_length=60, label='Full Name (Surname, First Name, Middle Name)')
#     # selected_strand = forms.TypedChoiceField(label="Select Strand", choices=(
#     #     (strand.id, strand.track.track_name + " - " + strand.strand_name) for strand in shs_strand.objects.select_related('track').exclude(is_deleted=True)
#     # ), coerce=str, required=False)
#     home_address = forms.CharField(
#         max_length=50, label='Home address')
#     age = forms.IntegerField(label="Age", min_value=1,
#                              max_value=100)
#     contact_number = forms.CharField(
#         label="Contact Number", widget=forms.NumberInput, validators=[validate_cp_number])
#     card = forms.ImageField(
#         label="Report card", help_text="Report card from previous year or quarter", required=False)
#     profile_image = forms.ImageField(
#         label="Student Photo", help_text="White background with no filters", required=False)


class makeDocumentRequestForm(forms.Form):
    documents = forms.TypedChoiceField(
        label="Document Type", choices=studentDocument.activeObjects.values_list("pk", "documentName"), coerce=str)
    scheduled_date = forms.DateField(label="Schedule", validators=[
                                     validate_schedule], widget=forms.DateInput(attrs={'type': 'date'}))


class makeDocumentRequestForm(forms.Form):
    documents = forms.CharField(max_length=50, disabled=True)
    scheduled_date = forms.DateField(label="Schedule", validators=[
                                     validate_schedule], widget=forms.DateInput(attrs={'type': 'date'}))
