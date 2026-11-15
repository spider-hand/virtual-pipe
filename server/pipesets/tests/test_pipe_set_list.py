from datetime import timedelta
from uuid import UUID

import pytest
from django.contrib.gis.geos import LineString
from django.utils import timezone

from pipesets.models import Pipe, PipeSet

pytestmark = pytest.mark.django_db


def test_list_pipesets_returns_successful_sets_with_their_own_geometry_bounds(client):
    older = PipeSet.objects.create(name="First created")
    newer = PipeSet.objects.create(name="Second created")
    PipeSet.objects.filter(pk=older.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    for status in [PipeSet.Status.PENDING, PipeSet.Status.FAILED]:
        PipeSet.objects.create(name=status, status=status)

    Pipe.objects.create(pipeset=older, geometry=LineString((130, 33), (131, 34)))
    Pipe.objects.create(pipeset=newer, geometry=LineString((138, 35), (139, 36)))
    Pipe.objects.create(pipeset=newer, geometry=LineString((139, 34), (140, 35)))

    response = client.get("/api/pipesets/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(newer.pk), "name": newer.name, "bounds": [138, 34, 140, 36]},
        {"id": str(older.pk), "name": older.name, "bounds": [130, 33, 131, 34]},
    ]


def test_list_pipesets_breaks_timestamp_ties_by_id_and_orders_undated_sets_by_name(
    client,
):
    first = PipeSet.objects.create(id=UUID(int=1), name="Zed")
    second = PipeSet.objects.create(id=UUID(int=2), name="Abe")
    legacy_z = PipeSet.objects.create(id=UUID(int=3), name="Zed legacy")
    legacy_a = PipeSet.objects.create(id=UUID(int=4), name="Abe legacy")
    PipeSet.objects.filter(pk__in=[legacy_z.pk, legacy_a.pk]).update(created_at=None)
    PipeSet.objects.filter(pk=second.pk).update(created_at=first.created_at)

    response = client.get("/api/pipesets/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(pipeset.pk), "name": pipeset.name, "bounds": None}
        for pipeset in [first, second, legacy_a, legacy_z]
    ]


def test_list_pipesets_returns_empty_list_when_no_pipesets_exist(client):
    response = client.get("/api/pipesets/")

    assert response.status_code == 200
    assert response.json() == []
