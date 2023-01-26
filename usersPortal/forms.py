from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from adminportal.models import *

User = get_user_model()


def validate_emailIntegrity(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError(
            f"{email} is already in use! Try again with different email.")


def validate_username(name):
    regex_name = re.compile(r""" ([a-z\s]+) """, re.VERBOSE | re.IGNORECASE)

    res = regex_name.fullmatch(name)

    if not res:
        raise ValidationError(
            "Username must be a plain texts. Spaces are allowed.")


class accountRegistrationForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_emailIntegrity])
    display_name = forms.CharField(
        label="Username", max_length=25, validators=[validate_username])
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
