from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokenGenerators import generate_enrollment_token
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from django.conf import settings
import numpy as np


def enrollment_emails_loop(request, admissionObj):
    mail_subject = "Enrollment Application"
    message = render_to_string("registrarportal/emailTemplates/enrollmentEmail.html", {
        "user_name": admissionObj.admission_owner.display_name,
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(admissionObj.pk)),
        "token": generate_enrollment_token.make_token(admissionObj),
        "expiration_date": (timezone.now() + relativedelta(seconds=settings.ENROLLMENT_TOKEN_TIMEOUT)).strftime("%A, %B %d, %Y - %I:%M: %p"),
    })
    email = EmailMessage(mail_subject, message, to=[
                         admissionObj.admission_owner.email])
    try:
        email.send()
        return True
    except Exception as e:
        return False


def send_enrollment_link(request, admissionObjs):
    try:
        loop_requests = [request for item in admissionObjs]
        emails = list(map(enrollment_emails_loop,
                      loop_requests, admissionObjs))

        messages.success(
            request, f"{emails.count(True)} out of {np.size(emails)} enrollment token has been sent.")
        return True
    except Exception as e:
        raise ValidationError(
            {'emailToken_failed': _(e)}
        )
