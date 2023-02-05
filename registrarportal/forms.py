from django import forms
from django.core.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def validate_startDate(date):
    if date < date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous date.")


def validate_endDate(date):
    if date <= date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous or current date.")


class add_schoolyear_form(forms.Form):
    start_on = forms.DateField(label="Start Date", validators=[
                               validate_startDate], widget=forms.DateInput(attrs={'type': 'date'}))
    until = forms.DateField(label="End Date", validators=[
                            validate_endDate], widget=forms.DateInput(attrs={'type': 'date'}))
