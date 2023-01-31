from django.db import models
from adminportal.models import studentDocument
from django.contrib.auth import get_user_model

User = get_user_model()


class documentRequest(models.Model):
    document = models.ForeignKey(
        studentDocument, on_delete=models.RESTRICT, related_name="documentRequestDetails")
    request_by = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="documentRequestedBy")
    scheduled_date = models.DateField()
    date_created = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_date"]
        unique_together = ["document", "scheduled_date"]

    def __str__(self):
        return f"{self.document.documentName} Request by - {self.request_by.display_name}"
