from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from datetime import time, datetime
from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36


class enrollment_token_generator(PasswordResetTokenGenerator):
    def check_token(self, enrObj, token):
        """
        Check that a password reset token is correct for a given user.
        """

        if not (enrObj and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
            # RemovedInDjango40Warning.
            legacy_token = len(ts_b36) < 4
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(enrObj, ts), token):
            # RemovedInDjango40Warning: when the deprecation ends, replace
            # with:
            #   return False
            if not constant_time_compare(
                self._make_token_with_timestamp(enrObj, ts, legacy=True),
                token,
            ):
                return False

        # RemovedInDjango40Warning: convert days to seconds and round to
        # midnight (server time) for pre-Django 3.1 tokens.
        now = self._now()
        if legacy_token:
            ts *= 24 * 60 * 60
            ts += int((now - datetime.combine(now.date(), time.min)).total_seconds())
        # Check the timestamp is within limit.
        if (self._num_seconds(now) - ts) > settings.ENROLLMENT_TOKEN_TIMEOUT:
            return False

        return True

    def _make_hash_value(self, enrObj, timestamp):
        return (
            six.text_type(enrObj.pk) + six.text_type(timestamp) + six.text_type(enrObj.admission_owner.id) + six.text_type(enrObj.first_name) + six.text_type(enrObj.is_accepted) +
            six.text_type(enrObj.admission_sy.id) + six.text_type(enrObj.type) + six.text_type(
                enrObj.is_denied) + six.text_type(enrObj.with_enrollment) + six.text_type(enrObj.created_on)
        )


generate_enrollment_token = enrollment_token_generator()
