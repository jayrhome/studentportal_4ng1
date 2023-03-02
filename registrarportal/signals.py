from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import student_admission_details, admission_batch, student_enrollment_details, enrollment_batch
from django.db.models import Case, When, Value, Count, Q, F


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


@receiver(post_save, sender=student_enrollment_details)
def enrollmentBatch(sender, instance, created, **kwargs):
    if created:
        if instance.year_level == '11':
            get_batches = enrollment_batch.objects.filter(sy=instance.enrolled_school_year, section__assignedStrand=instance.strand).alias(
                count_members=Count("members", filter=Q(members__is_denied=False))).exclude(count_members__gte=F("section__allowedPopulation")).first()

            if get_batches:
                get_batches.section.add(instance)
                get_batches.save()

            else:
                # get min member val, remove others
                pass
