from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Count, Q
from . forms import *
from . email_token import *
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import account_activation_token, password_reset_token
from ratelimit.decorators import ratelimit
from adminportal.models import *
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.db import IntegrityError


User = get_user_model()


def not_authenticated_user(user):
    return not user.is_authenticated


@login_required(login_url="usersPortal:login")
def logout_user(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse("usersPortal:login"))


@method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
class create_useraccount(FormView):
    template_name = "usersPortal/accountRegistration.html"
    form_class = accountRegistrationForm
    success_url = "/users/login/"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        display_name = form.cleaned_data["display_name"]
        password = form.cleaned_data["password"]
        confirmpassword = form.cleaned_data["confirmpassword"]

        try:
            if password == confirmpassword:
                user = User.objects.create_user(
                    email=email,
                    display_name=display_name,
                    password=password
                )
                # createAccount_activationLink(self.request, user)
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except ValidationError as e:
            match list(e.message_dict.keys())[0]:
                case ("invalid_email" | "emailToken_failed") as get_error_message:
                    messages.error(
                        self.request, e.message_dict[get_error_message][0])
                    return self.form_invalid(form)
                case _:
                    messages.error(
                        self.request, "An error has occurred. Please try again.")
                    return self.form_invalid(form)
        except Exception as e:
            messages.warning(
                self.request, "An error has occurred while submitting your data. Try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Account Registration"
        return context


# When user click the email authentication link
@user_passes_test(not_authenticated_user, login_url="studentportal:index")
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        user.refresh_from_db()

        if not User.update_lastUserTokenRequest(user):
            pass

        messages.success(request, "Your account is now activated.")
    else:
        messages.error(request, "Activation link is no longer valid!")

    return HttpResponseRedirect(reverse("usersPortal:login"))


@method_decorator(user_passes_test(not_authenticated_user, login_url="studentportal:index"), name="dispatch")
class login(FormView):
    template_name = "usersPortal/loginTemplates/login.html"
    form_class = loginForm
    success_url = "/"

    def get_success_url(self):
        # Custom redirection according to user type
        if self.request.user.is_superuser:
            return "/School_admin/"
        elif self.request.user.is_registrar:
            return super().get_success_url()
        elif self.request.user.validator_account:
            return super().get_success_url()
        else:
            return super().get_success_url()

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)

        if user is not None:
            auth_login(self.request, user)
            messages.success(
                self.request, f"You're now logged-in as {user.display_name}.")
            return super().form_valid(form)
        else:
            try:
                user_details = User.objects.get(email=email, is_active=False)
                if user_details.check_password(password):
                    return self.activate_account_request(self.request, user_details.display_name, email)
                messages.warning(
                    self.request, "Email or Password is incorrect. Try again.")
                return self.form_invalid(form)
            except Exception as e:
                messages.warning(
                    self.request, "Email or Password is incorrect. Try again.")
                return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Login"
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def activate_account_request(self, request, name, email):
        return render(request, "usersPortal/loginTemplates/activate_account_request.html", {"name": name, "email": email})


@method_decorator(user_passes_test(not_authenticated_user, login_url="studentportal:index"), name="dispatch")
class request_newAccountActivationToken(FormView):
    template_name = "usersPortal/loginTemplates/requestNewActivationToken.html"
    form_class = loginForm
    success_url = "/users/login/"

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            if User.objects.get(email=email, is_active=False).check_password(password):

                if not User.update_lastUserTokenRequest(User.objects.get(email=email)):
                    pass

                # createAccount_activationLink(self.request, user.objects.get(email=email))
                messages.success(
                    self.request, "The new authentication link has been sent to your account.")
                return super().form_valid(form)
            messages.warning(
                self.request, "Incorrect email or password. Try again.")
            return self.form_invalid(form)
        except User.DoesNotExist:
            messages.warning(self.request, f"{email} does not exist.")
            return self.form_invalid(form)
        except (ValidationError, Exception) as e:
            messages.error(
                self.request, "An error has occurred while submitting your data. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Request Token"
        return context


@method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
class forgotPassword(FormView):
    template_name = "usersPortal/forgotPassword/forgotPassword.html"
    form_class = forgotPasswordForm
    success_url = "/users/login/"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            if User.objects.filter(email=email, is_active=True).exists():
                user = User.objects.get(email=email)

                if not User.update_lastUserTokenRequest(user):
                    pass

                user.refresh_from_db()
                # forgotPassword_resetLink(self.request, user)
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Email does not exist! Try again.")
                return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request, "An error has occurred while submitting your data. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Forgot Password"
        return context


# When user click the password reset link
@method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
class passwordReset(FormView):
    template_name = "studentportal/password_reset_form.html"
    form_class = makeNewPasswordForm
    success_url = "/users/login/"

    def dispatch(self, request, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
            user = User.objects.get(pk=uid)
            self.user_obj = user
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and password_reset_token.check_token(user, self.kwargs['token']):
            # Return true if token is still valid
            return super().dispatch(request, *args, **kwargs)
        else:
            # if there's no user found, or the token is no longer valid, or both.
            messages.error(
                self.request, "Password reset link is no longer valid!")
            return HttpResponseRedirect(reverse("usersPortal:login"))

    def form_valid(self, form):
        password = form.cleaned_data["password"]
        confirmpassword = form.cleaned_data["confirmpassword"]

        try:
            if password == confirmpassword:
                if User.objects.filter(pk=self.user_obj.id).exists():
                    user = User.objects.get(pk=self.user_obj.id)

                    if not User.user_changePassword(user, confirmpassword):
                        pass

                    messages.success(
                        self.request, "Password changed successfully.")
                    return super().form_valid(form)
                else:
                    messages.error(self.request, "User no longer exists.")
                    return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except Exception as e:
            self.user_obj.refresh_from_db()
            if password_reset_token.check_token(self.user_obj, self.kwargs['token']):
                messages.error(
                    self.request, "An error occurred while submitting your date. Please try again.")
                return self.form_invalid(form)
            else:
                messages.error(self.request, "Reset token is no longer valid.")
                return super().form_valid(form)
