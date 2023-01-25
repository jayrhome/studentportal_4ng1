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


@login_required(login_url="")
def logout_user(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse(""))


@method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
class create_useraccount(FormView):
    template_name = "usersPortal/accountRegistration.html"
    form_class = accountRegistrationForm
    success_url = "/"

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
        context["title"] = "Newfangled Senior High School"
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
        user.last_user_token_request = timezone.now()
        user.save()

        messages.success(request, "Your account is now activated.")
    else:
        messages.error(request, "Activation link is no longer valid!")

    return HttpResponseRedirect(reverse("studentportal:login"))


# @method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
# class password_reset(FormView):
#     template_name = "studentportal/password_reset.html"
#     form_class = resetaccountForm
#     success_url = "/login/"

#     def form_valid(self, form):
#         email = form.cleaned_data["email"]
#         try:
#             if User.objects.filter(email=email, is_active=True).exists():
#                 user = User.objects.get(email=email)
#                 user.save()
#                 user.refresh_from_db()
#                 send_password_reset_link(self.request, user, email)
#                 return super().form_valid(form)
#             else:
#                 messages.warning(
#                     self.request, "Email does not exist. Try again.")
#                 return self.form_invalid(form)
#         except:
#             messages.error(
#                 self.request, "An error occurred while submitting your data. Please try again.")
#             return self.form_invalid(form)

#     def form_invalid(self, form):
#         return super().form_invalid(form)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "Newfangled Senior High School"
#         return context


# # When user click the password reset link
# @method_decorator([user_passes_test(not_authenticated_user, login_url="studentportal:index"), ratelimit(key='ip', rate='0/s')], name="dispatch")
# class password_reset_form(FormView):
#     template_name = "studentportal/password_reset_form.html"
#     form_class = resetpasswordForm
#     success_url = "/login/"

#     def dispatch(self, request, *args, **kwargs):
#         try:
#             uid = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
#             user = User.objects.get(pk=uid)
#             self.user_obj = user
#         except(TypeError, ValueError, OverflowError, User.DoesNotExist):
#             user = None

#         if user is not None and password_reset_token.check_token(user, self.kwargs['token']):
#             return super().dispatch(request, *args, **kwargs)
#         else:
#             messages.error(
#                 self.request, "Password reset link is no longer valid!")
#             return HttpResponseRedirect(reverse("studentportal:login"))

#     def form_valid(self, form):
#         password = form.cleaned_data["password"]
#         confirmpassword = form.cleaned_data["confirmpassword"]

#         try:
#             if password == confirmpassword:
#                 if User.objects.filter(pk=self.user_obj.id).exists():
#                     user = User.objects.get(pk=self.user_obj.id)
#                     user.set_password(password)
#                     user.save()
#                     messages.success(
#                         self.request, "Password changed successfully.")
#                     return super().form_valid(form)
#                 else:
#                     messages.error(self.request, "User no longer exists.")
#                     return super().form_valid(form)
#             else:
#                 messages.warning(
#                     self.request, "Password and Confirm Password did not match.")
#                 return self.form_invalid(form)
#         except:
#             self.user_obj.refresh_from_db()
#             if password_reset_token.check_token(self.user_obj, self.kwargs['token']):
#                 messages.error(
#                     self.request, "An error occurred while submitting your date. Please try again.")
#                 return self.form_invalid(form)
#             else:
#                 messages.error(self.request, "Reset token is no longer valid.")
#                 return super().form_valid(form)
