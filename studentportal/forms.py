from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from adminportal.models import *

User = get_user_model()


def validate_email(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already exists! Try again.")


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
            "Username should be a plain texts. Spaces are allowed.")


def birthdate_validator(dt):
    if dt >= date.today():
        raise ValidationError("Invalid date.")


def boolean_choices():
    bool_choices = (
        (True, 'Yes'),
        (False, 'No'),
    )
    return bool_choices


class loginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50)
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)


class createaccountForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_email_chars, validate_email])
    display_name = forms.CharField(
        label="Username", max_length=25, validators=[validate_username])
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)
    confirmpassword = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput)


class resetaccountForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_email_chars])


class resetpasswordForm(forms.Form):
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)
    confirmpassword = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput)


class admission_personal_details(forms.Form):
    first_name = forms.CharField(label="First Name", max_length=20)
    middle_name = forms.CharField(label="Middle Name", max_length=20)
    last_name = forms.CharField(label="Last Name", max_length=20)
    sex = forms.ChoiceField(
        label="Sex", choices=student_admission_details.SexChoices.choices)
    birth_date = forms.DateField(label="Birthdate", validators=[
                                 birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))
    birthplace = forms.CharField(label="Place of birth", max_length=200)
    nationality = forms.CharField(label="Nationality", max_length=50)


class elementary_school_details(forms.Form):
    elem_name = forms.CharField(label="Elementary School Name", max_length=50)
    elem_address = forms.CharField(
        label="Elementary School Address", max_length=50)
    elem_region = forms.CharField(label="School Region", max_length=30)
    elem_year_completed = forms.DateField(label="Year Completed", validators=[
                                          birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))
    elem_pept_passer = forms.ChoiceField(
        label="PEPT Passer?", choices=boolean_choices())
    elem_ae_date_completion = forms.DateField(label="Date Completed", validators=[
                                              birthdate_validator], widget=forms.DateInput(attrs={'type': 'date'}))
    elem_community_learning_center = forms.CharField(
        label="Community Learning Center", max_length=50)
    elem_clc_address = forms.CharField(
        label="Community Learning Center Address", max_length=50)
