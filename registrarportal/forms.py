from django import forms
from django.core.exceptions import ValidationError
from datetime import date, datetime


def setup_form_DateValidation(date):
    if date <= date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous or current date.")


class add_schoolyear_form(forms.Form):
    start_on = forms.DateField(label="Start Date", validators=[
                               setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    until = forms.DateField(label="End Date", validators=[
                            setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
