from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from . models import shs_strand, shs_track

User = get_user_model()


def get_track():
    track = shs_track.objects.all()
    return track


track_choices = (
    (track.id, track.track_name) for track in get_track()
)


def validate_newStrand(strand):
    obj = shs_strand.objects.filter(strand_name=strand).first()
    if obj:
        if obj.is_deleted == False:
            raise ValidationError("%s already exist." % strand)


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
