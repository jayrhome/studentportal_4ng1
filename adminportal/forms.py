from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from . models import *
from datetime import date, datetime
from django.forms.widgets import DateInput

User = get_user_model()

ea_setup_choices = [
    (True, "Yes"),
    (False, "No"),
]


def validate_newStrand(strand):
    obj = shs_strand.objects.filter(strand_name=strand).first()
    if obj:
        if obj.is_deleted == False:
            raise ValidationError("%s already exist." % strand)


def setup_form_DateValidation(date):
    if date < date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous or current date.")


class add_shs_track(forms.Form):
    name = forms.CharField(label="Track Name", max_length=50)
    details = forms.CharField(label="Track Details", widget=forms.Textarea)


class add_strand_form(forms.Form):
    track = forms.CharField(label="Course Track", disabled=True)
    strand_name = forms.CharField(
        label="Strand", max_length=100, validators=[validate_newStrand])
    strand_details = forms.CharField(
        label="Strand Details", widget=forms.Textarea)


class edit_strand_form(forms.Form):
    track = forms.CharField(label="Course Track", disabled=True)
    strand_name = forms.CharField(
        label="Strand", max_length=100)
    strand_details = forms.CharField(
        label="Strand Details", widget=forms.Textarea)


class ea_setup_form(forms.Form):
    start_date = forms.DateField(label="Start Date", validators=[
                                 setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label="End Date", validators=[
                               setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
    display_now = forms.ChoiceField(
        label="Display Now?", widget=forms.RadioSelect, choices=ea_setup_choices)
