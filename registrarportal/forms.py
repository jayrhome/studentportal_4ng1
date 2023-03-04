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


def setup_form_DateValidation(date):
    if date <= date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous or current date.")


class add_schoolyear_form(forms.Form):
    start_on = forms.DateField(label="Start Date", validators=[
                               validate_startDate], widget=forms.DateInput(attrs={'type': 'date'}))
    until = forms.DateField(label="End Date", validators=[
                            validate_endDate], widget=forms.DateInput(attrs={'type': 'date'}))


class ea_setup_form(forms.Form):
    start_date = forms.DateField(label="Start Date", validators=[
                                 setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label="End Date", validators=[
                               setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    students_perBatch = forms.CharField(
        label="Number of applicants per batch", widget=forms.NumberInput, max_length=2)


class ea_setup_form2(forms.Form):
    end_date = forms.DateField(label="End Date", validators=[
                               setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    students_perBatch = forms.CharField(
        label="Number of applicants per batch", widget=forms.NumberInput, max_length=2)


# class extend_enrollment(forms.Form):
#     end_date = forms.DateField(label="End Date", validators=[
#                                setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
