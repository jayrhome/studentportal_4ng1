from multiprocessing.sharedctypes import Value
from django import template
from django.utils.safestring import SafeString

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})
