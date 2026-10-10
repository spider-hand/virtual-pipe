from django.db import models


class Pipeset(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        FAILED = "failed"
        COMPLETED = "completed"

    name = models.TextField()
    count = models.PositiveBigIntegerField()
    bbox = models.JSONField()
    status = models.CharField(max_length=9, choices=Status, default=Status.PENDING)
