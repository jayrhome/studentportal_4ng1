from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import user_profile
from django.contrib.auth import get_user_model
User = get_user_model()


@receiver(post_save, sender=User)
def create_UserProfile(sender, instance, created, **kwargs):
    if created:
        if instance.is_student:
            # If a model instance is inserted to the database table or if its a newly created record, and user type is student
            user_profile.objects.create(
                user=instance, first_name=instance.display_name)
