from django import forms
from django.core.exceptions import ValidationError


class add_shs_track(forms.Form):
    name = forms.CharField(label="Track Name", max_length=50)
    details = forms.CharField(label="Track Details", widget=forms.Textarea)
