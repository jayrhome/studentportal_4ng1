from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from datetime import date, datetime
from . models import user_profile
# from studentportal.forms import validate_username, birthdate_validator, validate_cp_number

User = get_user_model()


def validate_emailIntegrity(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError(
            f"{email} is already in use! Try again with different email.")


def validate_imageSize(picture):
    if picture.size > 2*1024*1024:
        raise ValidationError(
            "File size is too big. 2mb is the maximum allowed size.")


class accountRegistrationForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_emailIntegrity])
    display_name = forms.CharField(
        label="Username", max_length=25, validators=["studentportal.validate_username", ])
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)
    confirmpassword = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput)


class loginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50)
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)


class forgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50)


class makeNewPasswordForm(forms.Form):
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput)
    confirmpassword = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput)


class profileDetailsForm(forms.Form):
    first_name = forms.CharField(label="First Name", max_length=50)
    middle_name = forms.CharField(label="Middle Name", max_length=20)
    last_name = forms.CharField(label="Last Name", max_length=50)
    birth_date = forms.DateField(label="Birthdate", widget=forms.DateInput(
        attrs={'type': 'date'}), validators=["studentportal.birthdate_validator", ])
    sex = forms.TypedChoiceField(
        label="sex", choices=user_profile.sexChoices.choices, coerce=str)
    userContact = forms.CharField(
        label="Contact Number", widget=forms.NumberInput, validators=["studentportal.validate_cp_number"])
    userAddress = forms.CharField(label="Permanent Address", max_length=100)
    image = forms.ImageField(label="Profile Picture", help_text="Max of 2 MB size.", required=False,
                             widget=forms.ClearableFileInput(attrs={"style": "display:none;"}), validators=[validate_imageSize, ])


class changePasswordForm(forms.Form):
    oldpassword = forms.CharField(
        label="Old Password", widget=forms.PasswordInput)
    newpassword = forms.CharField(
        label="New Password", widget=forms.PasswordInput(attrs={"onkeydown": "np(this)"}))
    confirmpassword = forms.CharField(
        label="Confirm New Password", widget=forms.PasswordInput(attrs={"onkeydown": "cp(this)"}))
