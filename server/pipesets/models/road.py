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
