from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class AccountManager(BaseUserManager):
    def create_user(self, email, display_name, password):
        user = self.model(
            email=email, display_name=display_name, password=password)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, display_name, password):
        user = self.create_user(
            email=email, display_name=display_name, password=password)
        user.set_password(password)
        user.is_student = False
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
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
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    last_password_changed_date = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    objects = AccountManager()

    def get_short_name(self):
        return self.display_name

    def natural_key(self):
        return self.email

    def __str__(self):
        return self.email
