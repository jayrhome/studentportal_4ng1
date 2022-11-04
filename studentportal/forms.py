from site import getusersitepackages
from socket import fromshare
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re

User = get_user_model()


def validate_email(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already exists! Try again.")


def validate_email_chars(email):
    regex_email = re.compile(r"""^([a-z0-9_\.]+)
                            @
                            (gmail)
                            \.
                            (com)$
                            """, re.VERBOSE | re.IGNORECASE)
    res = regex_email.fullmatch(email)
    if not res:
        raise ValidationError("Invalid email address. Try again.")


def validate_username(name):
    regex_name = re.compile(r""" ([a-z\s]+) """, re.VERBOSE | re.IGNORECASE)

    res = regex_name.fullmatch(name)

    if not res:
        raise ValidationError(
            "Username should be a plain texts. Spaces are allowed.")


class loginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50)
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput, strip=True)


class createaccountForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_email_chars, validate_email])
    display_name = forms.CharField(
        label="Username", max_length=25, strip=True, validators=[validate_username])
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput, strip=True)
    confirmpassword = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput, strip=True)


class resetaccountForm(forms.Form):
    email = forms.EmailField(
        label="Email", max_length=50, validators=[validate_email_chars])
