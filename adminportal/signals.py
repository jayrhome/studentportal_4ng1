from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import schoolSections
from registrarportal.models import enrollment_batch


@receiver(post_save, sender=schoolSections)
def enrollmentBatch(sender, instance, created, **kwargs):
    if created:
        # Create new batch for newly-added sections, both grade 11 and 12 sections
        enrollment_batch.objects.create(sy=instance.sy, section=instance)
