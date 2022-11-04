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
from django.db import IntegrityError
from . forms import loginForm, createaccountForm, resetaccountForm
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import account_activation_token, password_reset_token
from ratelimit.decorators import ratelimit


User = get_user_model()


def not_authenticated_user(user):
    return not user.is_authenticated


class index(TemplateView):
    template_name = "studentportal/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return HttpResponseRedirect(reverse("adminportal:index"))
            elif request.user.is_teacher:
                return HttpResponseRedirect(reverse("teachersportal:index"))
            else:
                return super().dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


@login_required(login_url="studentportal:login")
def logout_user(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse("studentportal:login"))


@method_decorator(user_passes_test(not_authenticated_user, login_url="studentportal:index"), name="dispatch")
class login(FormView):
    template_name = "studentportal/login.html"
    form_class = loginForm

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
                    # Send authentication email for is_active=False account.
                    return self.activate_account_request(self.request, user_details.display_name, email)

                messages.warning(
                    self.request, "Email or Password is incorrect. Try again.")
                return self.form_invalid(form)
            except:
                messages.warning(
                    self.request, "Email or Password is incorrect. Try again.")
                return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Account Login"
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def activate_account_request(self, request, name, email):
        return render(request, "studentportal/activate_account_request.html", {"name": name, "email": email})

    def get_success_url(self):
        return "/School_admin/" if self.request.user.is_superuser else "/"


@method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
class create_useraccount(FormView):
    template_name = "studentportal/create_user.html"
    form_class = createaccountForm
    success_url = "/login/"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        display_name = form.cleaned_data["display_name"]
        password = form.cleaned_data["password"]
        confirmpassword = form.cleaned_data["confirmpassword"]

        try:
            if User.objects.filter(email=email).exists():
                messages.warning(
                    self.request, "Email is already taken! Try again.")
                return self.form_invalid(form)

            if password == confirmpassword:
                user = User.objects.create_user(
                    email=email,
                    display_name=display_name,
                    password=password
                )
                send_activation_link(self.request, user, email)
                return super().form_valid(form)

            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except IntegrityError:
            return super().form_valid(form)
        except:
            messages.warning(
                self.request, "An error occurred while submitting your data. Try again.")
            return super().form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Account Registration"
        return context


def send_activation_link(request, user, email):
    mail_subject = "Activate your account"
    message = render_to_string("studentportal/activate_account.html", {
        "user": user.display_name,
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": account_activation_token.make_token(user),
        "protocol": "https" if request.is_secure() else "http"
    })
    email = EmailMessage(mail_subject, message, to=[email])

    if email.send():
        messages.success(
            request, f"Hi {user.display_name}, we sent a confirmation link to {user.email}. You can click the link to activate your account.")
    else:
        messages.error(
            request, f"Your activation link is not sent to {user.email}!")


def activate_account(request, uidb64, token):

    if request.user.is_authenticated:
        auth_logout(request)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        messages.error(request, "Activation link is no longer valid.")
        return HttpResponseRedirect(reverse("studentportal:login"))

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Your account is now activated.")
    else:
        messages.error(request, "Activation link is no longer valid!")

    return HttpResponseRedirect(reverse("studentportal:login"))


@method_decorator(user_passes_test(not_authenticated_user, login_url="studentportal:index"), name="dispatch")
class password_reset(FormView):
    template_name = "studentportal/password_reset.html"
    form_class = resetaccountForm
    success_url = "/login/"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                send_password_reset_link(self.request, email, user)
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Email does not exist. Try again.")
                return super().form_invalid(form)
        except:
            messages.warning(
                self.request, "An error occurred while submitting your data. Please try again.")
            return super().form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Forgot Password"
        return context


def send_password_reset_link(request, email, user):
    mail_subject = "Password Reset"
    message = render_to_string("studentportal/password_reset_email_template.html", {
        "user": user.display_name,
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": password_reset_token.make_token(user),
        "protocol": "https" if request.is_secure() else "http"
    })
    email = EmailMessage(mail_subject, message, to=[email])

    if email.send():
        messages.success(
            request, f"A password reset link is sent to {user.email}. You can click the link to reset your account password.")
    else:
        messages.error(
            request, f"Your password reset link is not sent to {user.email}!")


class password_reset_form(FormView):
    template_name = "studentportal/password_reset_form.html"
