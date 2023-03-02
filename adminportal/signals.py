from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import schoolSections
from registrarportal.models import enrollment_batch


@receiver(post_save, sender=schoolSections)
def enrollmentBatch(sender, instance, created, **kwargs):
    if created:
        if instance.yearLevel == '11':
            enrollment_batch.objects.create(sy=instance.sy, section=instance)
