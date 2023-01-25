from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import account_activation_token, password_reset_token
from email_validator import validate_email, EmailNotValidError
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from django.conf import settings


def createAccount_activationLink(request, user_instance):
    mail_subject = "Activate your account"
    message = render_to_string("usersPortal/email_templates/account_activation.html", {
        "user_name": user_instance.display_name,
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(user_instance.pk)),
        "token": account_activation_token.make_token(user_instance),
        "expiration_date": (timezone.now() + relativedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)).strftime("%A, %B %d, %Y - %I:%M: %p"),
    })
    email = EmailMessage(mail_subject, message, to=[user_instance.email])

    try:
        email.send()
        messages.success(
            request, f"Hi {user_instance.display_name}, your email authentication link is sent to {user_instance.email}. Click it to validate your account.")
        return True
    except Exception as e:
        raise ValidationError(
            {'emailToken_failed': _(e)}
        )
