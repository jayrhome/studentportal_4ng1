from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from django.conf import settings


def email_requestDocument(request, user_instance, documentRequest):
    mail_subject = "Document Request"
    message = render_to_string("studentportal/email_templates/documentRequestSchedule.html", {
        "user_name": user_instance.display_name,
        "document": documentRequest["type"],
        "schedule": documentRequest["schedule"],
    })
    email = EmailMessage(mail_subject, message, to=[user_instance.email])

    try:
        email.send()
        return True
    except Exception as e:
        raise ValidationError(
            {'emailToken_failed': _(e)}
        )
