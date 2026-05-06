from django.db import models
from storybook.utils.models import DefaultFields


LOG_TYPE_CHOICES = [
    ('info', 'Info'),
    ('warning', 'Warning'),
    ('error', 'Error'),
    ('debug', 'Debug'),
    ('critical', 'Critical'),
]

class Log(DefaultFields):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, default='info')
    message = models.TextField()

    class Meta:
        db_table = 'logs'

    def __str__(self):
        return f"{self.title} ({self.type})"