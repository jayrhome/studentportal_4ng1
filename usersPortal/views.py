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
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import account_activation_token, password_reset_token
from ratelimit.decorators import ratelimit
from adminportal.models import *
from datetime import date, datetime
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import IntegrityError
from studentportal.views import student_access_only
from . models import *
from adminportal.views import superuser_only


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
            # messages.error(self.request, e)
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
            return "/Registrar/"
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

                # createAccount_activationLink(
                #     self.request, User.objects.get(email=email))
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
    template_name = "usersPortal/forgotPassword/makeNewPassword.html"
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


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class userAccountProfile(TemplateView):
    template_name = "usersPortal/profile/profileDetails.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Profile"

        get_userDetails = user_profile.get_userProfile(self.request.user)
        if get_userDetails:
            context["userDetails"] = {
                "first_name": get_userDetails.first_name,
                "middle_name": get_userDetails.middle_name,
                "last_name": get_userDetails.last_name,
                "birth_date": get_userDetails.birth_date,
                "sex": get_userDetails.get_sex_display(),
                "userimage": get_userDetails.profilePic[0] if get_userDetails.profilePic else "",
                "contactnum": get_userDetails.userContact[0] if get_userDetails.userContact else "",
                "useraddress": get_userDetails.userAddress[0] if get_userDetails.userAddress else "",
            }

        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(student_access_only, login_url="studentportal:index")], name="dispatch")
class updateAccountProfile(FormView):
    template_name = "usersPortal/profile/profileUpdate.html"
    success_url = "/users/Profile/"
    form_class = profileDetailsForm

    def get_initial(self):
        initial = super().get_initial()

        get_userprofile = user_profile.get_userProfile(self.request.user)

        if get_userprofile:
            get_userprofile.userContact = get_userprofile.userContact[
                0] if get_userprofile.userContact else ""
            get_userprofile.userAddress = get_userprofile.userAddress[
                0] if get_userprofile.userAddress else ""

        for index, fieldname in enumerate(list(self.form_class().declared_fields.keys())):
            match fieldname:
                case ("userContact" | "userAddress"):
                    initial[fieldname] = str(
                        getattr(get_userprofile, fieldname, ""))
                case "image":
                    pass
                case _:
                    initial[fieldname] = getattr(
                        get_userprofile, fieldname, "")
        return initial

    def form_valid(self, form):
        try:
            if form.has_changed():
                userProfile, is_created = user_profile.objects.get_or_create(
                    user=self.request.user)

                if is_created:
                    userProfile = user_profile.objects.get(
                        user=self.request.user)

                for index, field in enumerate(form.changed_data):
                    match field:
                        case "userContact":
                            try:
                                contact, isContactCreated = user_contactNumber.objects.get_or_create(
                                    contactNumber_of=userProfile, cellphone_number=form.cleaned_data[field])
                                if not isContactCreated:
                                    contact.save()
                            except (IntegrityError, Exception) as e:
                                messages.error(
                                    self.request, f"Contact Number {form.cleaned_data[field]} is already in use.")
                                return self.form_invalid(form)

                        case "userAddress":
                            try:
                                address, isAddressCreated = user_address.objects.get_or_create(
                                    location_of=userProfile, address=form.cleaned_data[field])
                                if not isAddressCreated:
                                    address.save()
                            except (IntegrityError, Exception) as e:
                                return self.form_invalid(form)

                        case "image":
                            image, isImageCreated = user_photo.objects.get_or_create(
                                photo_of=userProfile, image=form.cleaned_data[field])
                            if not isImageCreated:
                                image.save()

                        case _:
                            setattr(userProfile, field,
                                    form.cleaned_data[field])
                userProfile.save()
                return super().form_valid(form)

            return super().form_valid(form)
        except ValidationError as e:
            match list(e.message_dict.keys())[0]:
                # case ("photo_tooBig") as get_error_message:
                #     messages.error(
                #         self.request, e.message_dict[get_error_message][0])
                #     return self.form_invalid(form)
                case _:
                    messages.error(
                        self.request, "Failed to update your profile. Please try again.")
                    return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, "tangina")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Profile"

        try:
            a = user_profile.objects.get(user=self.request.user)
            context["userimage"] = a.user_pic.first()
        except:
            pass

        return context


@method_decorator(login_required(login_url="usersPortal:login"), name="dispatch")
class userChangePassword(FormView):
    template_name = "usersPortal/profile/changePassword.html"
    success_url = "/users/Profile/"
    form_class = changePasswordForm

    def get_success_url(self):
        # Custom redirection according to user type
        if self.request.user.is_superuser:
            return "/School_admin/"
        elif self.request.user.is_registrar:
            return "/Registrar/"
        elif self.request.user.validator_account:
            return super().get_success_url()
        else:
            return super().get_success_url()

    def form_valid(self, form):
        try:
            oldpassword = form.cleaned_data["oldpassword"]
            newpassword = form.cleaned_data["newpassword"]
            confirmpassword = form.cleaned_data["confirmpassword"]

            if newpassword == confirmpassword:
                if self.request.user.check_password(oldpassword):
                    self.request.user.set_password(newpassword)
                    self.request.user.save()
                    self.request.user.refresh_from_db()
                    messages.success(
                        self.request, "Password is changed successfully.")
                    return super().form_valid(form)

                messages.warning(self.request, "Old password is incorrect.")
                return self.form_invalid(form)
            messages.warning(
                self.request, "New password and confirm new password did not match. Try again.")
            return self.form_invalid(form)

        except Exception as e:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Change Password"
        return context


@method_decorator(login_required(login_url="usersPortal:login"), name="dispatch")
class authenticatedUser_resetPassword(TemplateView):
    template_name = "usersPortal/forgotPassword/passwordReset.html"
    http_method_names = ["get", "post"]

    def post(self, request, *args, **kwargs):
        try:
            if not User.update_lastUserTokenRequest(self.request.user):
                messages.error(
                    request, "Reset Password has failed! Please try again.")
                return HttpResponseRedirect(reverse("usersPortal:resetpassword"))
            self.request.user.refresh_from_db()
            # forgotPassword_resetLink(self.request, user)
            return HttpResponseRedirect(reverse("usersPortal:logout"))
        except Exception as e:
            messages.error(
                request, "Reset Password has failed! Please try again.")
            return HttpResponseRedirect(reverse("usersPortal:resetpassword"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Password Reset"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class create_adminAccount(FormView):
    template_name = "usersPortal/accountRegistration.html"
    success_url = "/users/create_adminAccount/"
    form_class = accountRegistrationForm

    def form_valid(self, form):
        try:
            email = form.cleaned_data["email"]
            display_name = form.cleaned_data["display_name"]
            password = form.cleaned_data["password"]
            confirmpassword = form.cleaned_data["confirmpassword"]

            if password == confirmpassword:
                admin_user = User.objects.create_superuser(
                    email=email,
                    display_name=display_name,
                    password=password
                )
                messages.success(
                    self.request, f"{email} is successfully created.")
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except ValidationError as e:
            match list(e.message_dict.keys())[0]:
                case ("invalid_email") as get_error_message:
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
            # messages.error(self.request, e)
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Admin Account"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class create_registrarAccount(FormView):
    template_name = "usersPortal/accountRegistration.html"
    success_url = "/users/create_registrarAccount/"
    form_class = accountRegistrationForm

    def form_valid(self, form):
        try:
            email = form.cleaned_data["email"]
            display_name = form.cleaned_data["display_name"]
            password = form.cleaned_data["password"]
            confirmpassword = form.cleaned_data["confirmpassword"]

            if password == confirmpassword:
                admin_user = User.objects.create_registrarAccount(
                    email=email,
                    display_name=display_name,
                    password=password
                )
                messages.success(
                    self.request, f"{email} is successfully created.")
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except ValidationError as e:
            match list(e.message_dict.keys())[0]:
                case ("invalid_email") as get_error_message:
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
            # messages.error(self.request, e)
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Registrar Account"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(superuser_only, login_url="registrarportal:dashboard")], name="dispatch")
class create_validatorAccount(FormView):
    template_name = "usersPortal/accountRegistration.html"
    success_url = "/users/create_validatorAccount/"
    form_class = accountRegistrationForm

    def form_valid(self, form):
        try:
            email = form.cleaned_data["email"]
            display_name = form.cleaned_data["display_name"]
            password = form.cleaned_data["password"]
            confirmpassword = form.cleaned_data["confirmpassword"]

            if password == confirmpassword:
                admin_user = User.objects.create_accountValidator(
                    email=email,
                    display_name=display_name,
                    password=password
                )
                messages.success(
                    self.request, f"{email} is successfully created.")
                return super().form_valid(form)
            else:
                messages.warning(
                    self.request, "Password and Confirm Password did not match.")
                return self.form_invalid(form)
        except ValidationError as e:
            match list(e.message_dict.keys())[0]:
                case ("invalid_email") as get_error_message:
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
            # messages.error(self.request, e)
            return self.form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Validator Account"
        return context
