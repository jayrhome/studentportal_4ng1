from django.db import models
from adminportal.models import studentDocument
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


class getActiveDocumentRequests(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(scheduled_date__gte=date.today(), is_cancelledByRegistrar=False)


class documentRequest(models.Model):
    document = models.ForeignKey(
        studentDocument, on_delete=models.RESTRICT, related_name="documentRequestDetails")
    request_by = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="documentRequestedBy")
    scheduled_date = models.DateField()
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    is_cancelledByRegistrar = models.BooleanField(default=False)

    objects = models.Manager()
    registrarObjects = getActiveDocumentRequests()

    class Meta:
        ordering = ["scheduled_date", "last_modified"]
        unique_together = ["document", "scheduled_date"]

    def __str__(self):
        return f"{self.document.documentName} Request by - {self.request_by.display_name}"
