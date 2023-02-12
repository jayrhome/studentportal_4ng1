from django.test import TestCase
from . models import *
from django.contrib.auth import get_user_model

user = get_user_model()


def getme():
    a = user_profile.get_userProfile(
        user.objects.get(email="vincenthan19@gmail.com"))
    return a
