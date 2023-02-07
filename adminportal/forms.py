from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from . models import *
from datetime import date, datetime
from django.forms.widgets import DateInput
from registrarportal.forms import validate_startDate

User = get_user_model()


def validate_newStrand(strand):
    obj = shs_strand.objects.filter(strand_name=strand).first()
    if obj:
        if obj.is_deleted == False:
            raise ValidationError("%s already exist." % strand)


def setup_form_DateValidation(date):
    if date <= date.today():
        raise ValidationError(
            "Invalid Date! Do not select the previous or current date.")


def validate_eventName_uniqueness(name):
    if school_events.ongoingEvents.filter(name__unaccent__icontains=name).exists():
        raise ValidationError(f"{name} is an ongoing event.")


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


# class ea_setup_form(forms.Form):
#     start_date = forms.DateField(label="Start Date", validators=[
#                                  setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))
#     end_date = forms.DateField(label="End Date", validators=[
#                                setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))


# class extend_enrollment(forms.Form):
#     end_date = forms.DateField(label="End Date", validators=[
#                                setup_form_DateValidation], widget=forms.DateInput(attrs={'type': 'date'}))


class makeDocument(forms.Form):
    documentName = forms.CharField(label="Document Name", max_length=50)


class addEventForm(forms.Form):
    name = forms.CharField(label="Event Name", max_length=100, validators=[
                           validate_eventName_uniqueness, ])
    start_on = forms.DateField(label="Start Date", validators=[
                               validate_startDate], widget=forms.DateInput(attrs={'type': 'date'}))


class updateEventForm(forms.Form):
    name = forms.CharField(label="Event Name", max_length=100)
    start_on = forms.DateField(label="Start Date", validators=[
                               validate_startDate], widget=forms.DateInput(attrs={'type': 'date'}))


class addSubjectForm(forms.Form):
    code = forms.CharField(label="Subject Code", max_length=20)
    title = forms.CharField(label="Subject Title", max_length=50)
