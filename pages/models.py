from django.db import models
from storybook.utils.models import DefaultFields


STATUS_CHOICES = [("pending", "Pending"), ("reviewed", "Reviewed"), ("resolved", "Resolved")]


class Contact(DefaultFields):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "contacts"

    def __str__(self):
        return f"{self.name} ({self.email})"
