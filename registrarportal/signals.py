from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import student_admission_details, admission_batch
from django.db.models import Case, When, Value, Count, Q


@receiver(post_save, sender=student_admission_details)
def admissionBatch(sender, instance, created, **kwargs):
    if created:
        get_batch = admission_batch.objects.alias(count_applicants=Count("members", filter=Q(
            members__is_accepted=False))).filter(sy=instance.admission_sy).exclude(count_applicants__gte=50).first()

        if not get_batch:
            get_batch = admission_batch.objects.create(
                sy=instance.admission_sy)

        get_batch.members.add(instance)
        get_batch.save()
