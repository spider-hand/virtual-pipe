import uuid

from django.contrib.gis.db import models


class RoadDataSetup(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued"
        DOWNLOADING = "downloading"
        IMPORTING = "importing"
        SUCCEEDED = "succeeded"
        FAILED = "failed"

    class Failure(models.TextChoices):
        QUEUE = "queue"
        DOWNLOAD = "download"
        IMPORT = "import"

    region = models.CharField(max_length=8)
    status = models.CharField(
        max_length=11, choices=Status.choices, default=Status.QUEUED
    )
    failure = models.CharField(max_length=8, choices=Failure.choices, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.Value(1),
                condition=models.Q(status__in=["queued", "downloading", "importing"]),
                name="only_one_active_road_data_setup",
            )
        ]


class PipeSet(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        SUCCEEDED = "succeeded"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    district_id = models.CharField(max_length=5, blank=True)
    prefecture_id = models.CharField(max_length=2, blank=True)
    attribute_set = models.ForeignKey(
        "AttributeSet", on_delete=models.PROTECT, null=True
    )
    status = models.CharField(
        max_length=9, choices=Status.choices, default=Status.SUCCEEDED
    )
    failure_reason = models.TextField(blank=True)


class Pipe(models.Model):
    """Use Django's integer primary key as the native PostGIS vector tile feature ID."""

    pipeset = models.ForeignKey(PipeSet, on_delete=models.CASCADE)
    geometry = models.LineStringField(srid=4326)
    attributes = models.JSONField(default=dict)


class AttributeSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    attributes = models.JSONField()
