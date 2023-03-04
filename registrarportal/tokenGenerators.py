from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from datetime import time, datetime
from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36


class enrollment_token_generator(PasswordResetTokenGenerator):

    def check_token(self, enrObj, token):
        """
        Check that a enrollment token is correct for a given user.
        """
        if not (enrObj and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(enrObj, ts, secret),
                token,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > settings.ENROLLMENT_TOKEN_TIMEOUT:
            return False

        return True

    def _make_hash_value(self, enrObj, timestamp):
        return (
            six.text_type(enrObj.pk) + six.text_type(timestamp) + six.text_type(enrObj.admission_owner.id) + six.text_type(enrObj.first_name) + six.text_type(enrObj.is_accepted) +
            six.text_type(enrObj.admission_sy.id) + six.text_type(enrObj.type) + six.text_type(
                enrObj.is_denied) + six.text_type(enrObj.with_enrollment) + six.text_type(enrObj.created_on)
        )


class re_enroll_token_generator(PasswordResetTokenGenerator):
    def check_token(self, inv_object, token):
        """
        Check that a enrollment token is correct for a given user.
        """
        if not (inv_object and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(inv_object, ts, secret),
                token,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > settings.ENROLLMENT_TOKEN_TIMEOUT:
            return False

        return True

    def _make_hash_value(self, inv_object, timestamp):
        return (six.text_type(inv_object.pk) + six.text_type(timestamp) + six.text_type(inv_object.invitation_to.admission_owner.id) + six.text_type(inv_object.is_accepted) + six.text_type(inv_object.modified_on))


generate_enrollment_token = enrollment_token_generator()
new_enrollment_token_for_old_students = re_enroll_token_generator()
