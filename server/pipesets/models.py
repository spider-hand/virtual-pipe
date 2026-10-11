from django.contrib.gis.db import models


class Pipeset(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        FAILED = "failed"
        COMPLETED = "completed"

    name = models.TextField()
    bbox = models.JSONField()
    status = models.CharField(max_length=9, choices=Status, default=Status.PENDING)

    @property
    def count(self):
        return self.pipes.count()


class Pipe(models.Model):
    geometry = models.LineStringField(srid=4326, dim=2)
    pipeset = models.ForeignKey(Pipeset, on_delete=models.CASCADE, related_name="pipes")
    attributes = models.JSONField(default=dict, blank=True)
