from unittest.mock import patch

import pytest
from django.db import connection

from pipesets.models import Pipe, Pipeset
from pipesets.tasks import generate_pipes

pytestmark = pytest.mark.django_db


@pytest.fixture
def road():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO osm_roads (way_id, highway, geometry)
            VALUES (1, 'residential',
                ST_GeomFromText('LINESTRING(138.99 35.005,139.02 35.005)', 4326)),
                (2, 'residential',
                ST_GeomFromText('LINESTRING(139.002 35.007,139.004 35.007)', 4326))
            """
        )


@pytest.fixture
def pipeset():
    return Pipeset.objects.create(name="Tokyo pipes", bbox=[139, 35, 139.01, 35.01])


def test_generates_one_pipe_per_clipped_road_within_bbox(pipeset, road):
    generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "completed"
    assert pipeset.pipes.count() == 2
    # Check every pipe stays inside the bbox, and their union equals all clipped roads.
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT bool_and(ST_CoveredBy(geometry,
                ST_MakeEnvelope(%s, %s, %s, %s, 4326))),
                ST_Equals(ST_UnaryUnion(ST_Collect(geometry)), (
                    SELECT ST_UnaryUnion(ST_Collect(ST_Intersection(geometry,
                        ST_MakeEnvelope(%s, %s, %s, %s, 4326))))
                    FROM osm_roads
                ))
            FROM pipesets_pipe
            WHERE pipeset_id = %s
            """,
            [*pipeset.bbox, *pipeset.bbox, pipeset.pk],
        )
        assert cursor.fetchone() == (True, True)


def test_covers_roads_shorter_than_one_metre(pipeset, road):
    pipeset.bbox = [139, 35, 139.000001, 35.006]
    pipeset.save()
    generate_pipes(pipeset.pk)
    assert pipeset.pipes.count() == 1


def test_does_not_duplicate_pipes_when_job_is_delivered_again(pipeset, road):
    generate_pipes(pipeset.pk)
    generate_pipes(pipeset.pk)
    assert pipeset.pipes.count() == 2


def test_fails_without_usable_roads(pipeset):
    with pytest.raises(ValueError, match="No roads"):
        generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "failed"
    assert not pipeset.pipes.exists()


def test_rolls_back_pipes_when_processing_fails(pipeset, road):
    with (
        patch.object(Pipeset, "save", side_effect=RuntimeError("Processing failed")),
        pytest.raises(RuntimeError, match="Processing failed"),
    ):
        generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "failed"
    assert not Pipe.objects.exists()


def test_generates_and_preserves_attributes(pipeset, road):
    pipeset.attribute_definitions = [
        {"name": "label", "type": "string", "min": 3, "max": 8},
        {"name": "diameter", "type": "number", "min": -10, "max": 10},
        {"name": "active", "type": "boolean"},
        {"name": "material", "type": "category", "categories": ["PVC", "steel"]},
        {"name": "empty", "type": "string", "min": 0, "max": 0},
        {"name": "fixed", "type": "number", "min": 42, "max": 42},
    ]
    pipeset.save()
    generate_pipes(pipeset.pk)
    original = list(pipeset.pipes.order_by("id").values_list("attributes", flat=True))
    for attributes in original:
        assert len(attributes) == 6
        assert 3 <= len(attributes["label"]) <= 8
        assert attributes["label"].isascii() and attributes["label"].isalnum()
        assert type(attributes["diameter"]) is int
        assert -10 <= attributes["diameter"] <= 10
        assert type(attributes["active"]) is bool
        assert attributes["material"] in {"PVC", "steel"}
        assert attributes["empty"] == ""
        assert attributes["fixed"] == 42
    generate_pipes(pipeset.pk)
    assert (
        list(pipeset.pipes.order_by("id").values_list("attributes", flat=True))
        == original
    )


def test_rolls_back_when_attribute_generation_fails(pipeset, road):
    pipeset.attribute_definitions = [{"name": "a", "type": "boolean"}]
    pipeset.save()
    with (
        patch(
            "pipesets.tasks.generate_attributes",
            side_effect=RuntimeError("Attribute failure"),
        ),
        pytest.raises(RuntimeError, match="Attribute failure"),
    ):
        generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "failed"
    assert not pipeset.pipes.exists()
