import uuid

from django.contrib.gis.db import models


class PipeSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)


class Pipe(models.Model):
    """Use Django's integer primary key as the native PostGIS vector tile feature ID."""

    pipeset = models.ForeignKey(PipeSet, on_delete=models.CASCADE)
    geometry = models.LineStringField(srid=4326)


class AttributeSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    attributes = models.JSONField()
