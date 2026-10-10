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
                ST_GeomFromText('LINESTRING(138.99 35.005,139.02 35.005)', 4326))
            """
        )


@pytest.fixture
def pipeset():
    return Pipeset.objects.create(
        name="Tokyo pipes", count=25, bbox=[139, 35, 139.01, 35.01]
    )


def test_generates_requested_pipes_on_roads_within_bbox(pipeset, road):
    generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "completed"
    assert pipeset.pipes.count() == pipeset.count
    # Check every pipe is 1–500 metres long, entirely inside the bbox (including
    # its boundary), and within 0.1 metres of the road.
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT bool_and(
                ST_Length(pipe.geometry::geography) BETWEEN 1 AND 500
                AND ST_CoveredBy(pipe.geometry, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
                AND ST_CoveredBy(pipe.geometry,
                    ST_Buffer(road.geometry::geography, 0.1)::geometry)
            )
            FROM pipesets_pipe AS pipe CROSS JOIN osm_roads AS road
            WHERE pipe.pipeset_id = %s
            """,
            [*pipeset.bbox, pipeset.pk],
        )
        assert cursor.fetchone()[0]


def test_does_not_duplicate_pipes_when_job_is_delivered_again(pipeset, road):
    generate_pipes(pipeset.pk)
    generate_pipes(pipeset.pk)
    assert pipeset.pipes.count() == pipeset.count


def test_fails_without_usable_roads(pipeset):
    with pytest.raises(ValueError, match="No roads"):
        generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "failed"
    assert not pipeset.pipes.exists()


def test_fails_when_no_valid_pipe_can_be_generated(pipeset, road):
    with (
        patch("pipesets.tasks.uniform", return_value=0),
        pytest.raises(
            ValueError, match="Could not generate a pipe between 1 and 500 metres"
        ),
    ):
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
