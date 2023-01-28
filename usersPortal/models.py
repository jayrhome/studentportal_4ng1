from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from email_validator import validate_email, EmailNotValidError
from django.utils import timezone
from django.db.models import Prefetch


class AccountManager(BaseUserManager):
    def create_user(self, email, display_name, password):
        user = self.model(
            email=email, display_name=display_name, password=password)
        user.is_student = True
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, display_name, password):
        user = self.model(
            email=email, display_name=display_name, password=password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_registrarAccount(self, email, display_name, password):
        user = self.model(
            email=email, display_name=display_name, password=password)
        user.is_active = True
        user.is_registrar = True
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_accountValidator(self, email, display_name, password):
        user = self.model(
            email=email, display_name=display_name, password=password)
        user.is_active = True
        user.validator_account = True
        user.set_password(password)
        user.save(using=self.db)
        return user

    def get_by_natural_key(self, email_):
        print(email_)
        return self.get(email=email_)


# email: admin@gmail.com  password: admin
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=50)
    display_name = models.CharField(max_length=25)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_registrar = models.BooleanField(default=False)
    validator_account = models.BooleanField(default=False)
    last_user_token_request = models.DateTimeField(default=timezone.now)
    last_password_changed_date = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    objects = AccountManager()

    class Meta:
        permissions = [
            ('can_validate_enrollment_admission',
             'Can validate enrollment and admission'),
        ]

    def get_short_name(self):
        return self.display_name

    def natural_key(self):
        return self.email

    def __str__(self):
        return self.email

    def clean(self):
        try:
            validate_email(self.email)

            # if self.is_student and not (self.is_staff or self.is_superuser or self.is_registrar or self.validator_account):
            #     pass
            # elif self.is_staff and not (self.is_student or self.is_registrar or self.validator_account):
            #     pass
            # elif self.is_superuser and not (self.is_student or self.is_registrar or self.validator_account):
            #     pass
            # elif self.is_registrar and not (self.is_staff or self.is_superuser or self.is_student or self.validator_account):
            #     pass
            # elif self.validator_account and not (self.is_staff or self.is_superuser or self.is_student or self.is_registrar):
            #     pass
            # else:
            #     raise ValidationError(
            #         {'invalid_usertype': _(
            #             'You are not allowed to have this kind of user type.')}
            #     )
        except EmailNotValidError as e:
            raise ValidationError(
                {'invalid_email': _('Email is invalid. Try again.')}
            )
        except Exception as e:
            raise ValidationError(
                {'email_exception_error': _(e)}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def update_lastUserTokenRequest(cls, userInstance):
        try:
            with transaction.atomic():
                get_userInstance = cls.objects.select_for_update().get(pk=userInstance.id)
                get_userInstance.last_user_token_request = timezone.now()
                get_userInstance.save()
            # return (get_userInstance.last_user_token_request).strftime("%A, %B %d, %Y - %I:%M: %p")
            return True
        except Exception as e:
            return False

    @classmethod
    def user_changePassword(cls, userInstance, raw_password):
        try:
            with transaction.atomic():
                get_userInstance = cls.objects.select_for_update().get(pk=userInstance.id)
                get_userInstance.set_password(raw_password)
                get_userInstance.save()
            return True
        except Exception as e:
            return False


class user_address(models.Model):
    address = models.CharField(max_length=100)
    location_of = models.ForeignKey(
        "user_profile", on_delete=models.RESTRICT, related_name="address")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]
        unique_together = ['address', 'location_of']

    def __str__(self):
        return self.address


class user_contactNumber(models.Model):
    contactNumber_of = models.ForeignKey(
        "user_profile", on_delete=models.RESTRICT, related_name="contactNumber")
    cp_number_regex = RegexValidator(regex=r"^(09)([0-9]{9})$")
    cellphone_number = models.CharField(
        max_length=11, unique=True, validators=[cp_number_regex])
    date_created = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return self.cellphone_number


class user_photo(models.Model):
    photo_of = models.ForeignKey(
        "user_profile", on_delete=models.RESTRICT, related_name="user_pic")
    image = models.ImageField(
        default="user_images/default_male.png", upload_to="user_images/%Y/%m/%d/")
    date_created = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return self.photo_of.first_name

    # def clean(self):
    #     try:
    #         if self.image.size > 2*1024*1024:
    #             raise ValidationError(
    #                 {'photo_tooBig': _(
    #                     "File size is too large. 2mb is the maximum allowed size.")}
    #             )
    #     except Exception as e:
    #         raise ValidationError(
    #             {'photo_validationError_failed': _(e)}
    #         )

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     return super().save(*args, **kwargs)


class user_profile(models.Model):
    class sexChoices(models.TextChoices):
        Male = 'M', _('Male')
        Female = 'F', _('Female')

    user = models.OneToOneField(
        User, on_delete=models.RESTRICT, related_name="profile")
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=50, null=True)
    birth_date = models.DateField(null=True)
    sex = models.CharField(max_length=2, choices=sexChoices.choices, null=True)
    date_created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name

    def user_age(self):
        if self.birth_date:
            return relativedelta(date.today(), self.birth_date).years

    @classmethod
    def get_userProfile(cls, userInstance):
        obj = cls.objects.filter(user__id=userInstance.id).prefetch_related(
            Prefetch("user_pic", queryset=user_photo.objects.only(
                "image"), to_attr="profilePic"),
            Prefetch("contactNumber", queryset=user_contactNumber.objects.only(
                "cellphone_number"), to_attr="userContact"),
            Prefetch("address", queryset=user_address.objects.only(
                "address"), to_attr="userAddress"),
        )
        return obj.first()
