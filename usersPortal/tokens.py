from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active) +
            six.text_type(user.last_user_token_request)
        )


class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.last_password_changed_date) +
            six.text_type(user.last_user_token_request) +
            six.text_type(user.last_password_changed_date)
        )


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
