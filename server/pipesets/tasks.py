from random import randint, uniform

from celery import shared_task
from django.db import connection, transaction

from .models import Pipeset


@shared_task(ignore_result=True)
def generate_pipes(pipeset_id):
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            pipeset = Pipeset.objects.select_for_update().get(pk=pipeset_id)
            if pipeset.status != Pipeset.Status.PENDING:
                return
            # Prepare road candidates once so each pipe can reuse them without
            # searching and clipping the source roads again. Store geometry and
            # length in a temporary table with sequential IDs for random selection.
            cursor.execute(
                """
                CREATE TEMP TABLE pipe_roads (
                    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    geometry geometry(LineString, 4326),
                    length double precision
                ) ON COMMIT DROP
                """
            )
            # Find roads overlapping the bbox and cut away the parts outside it.
            # Store each resulting line separately, with its length in metres,
            # keeping only lines at least one metre long. Leave osm_roads unchanged.
            cursor.execute(
                """
                INSERT INTO pipe_roads (geometry, length)
                SELECT part.geom, ST_Length(part.geom::geography)
                FROM osm_roads
                CROSS JOIN LATERAL ST_Dump(ST_CollectionExtract(
                    ST_Intersection(geometry, ST_MakeEnvelope(%s, %s, %s, %s, 4326)), 2
                )) AS part
                WHERE geometry && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                    AND ST_Length(part.geom::geography) >= 1
                """,
                [*pipeset.bbox, *pipeset.bbox],
            )
            # Count the candidates for random selection; fail if none are usable.
            cursor.execute("SELECT count(*) FROM pipe_roads")
            road_count = cursor.fetchone()[0]
            if not road_count:
                raise ValueError("No roads of at least one metre within the bbox.")

            # Generate the requested number of pipes at random positions and lengths on roads.
            for _ in range(pipeset.count):
                # Retry up to 100 times if clipping leaves no valid 1–500 metre line.
                for _ in range(100):
                    cursor.execute(
                        "SELECT length FROM pipe_roads WHERE id = %s",
                        [road_id := randint(1, road_count)],
                    )
                    road_length = cursor.fetchone()[0]
                    length = uniform(1, min(500, road_length))
                    start = uniform(0, road_length - length) / road_length
                    # Extract a road segment, clip it to the bbox, and save the longest
                    # valid piece as one pipe. Return its ID to confirm insertion.
                    cursor.execute(
                        """
                        WITH segment AS (
                            SELECT ST_LineSubstring(geometry::geography, %s, %s)::geometry
                                AS geometry
                            FROM pipe_roads WHERE id = %s
                        ), clipped AS (
                            SELECT part.geom AS geometry
                            FROM segment
                            CROSS JOIN LATERAL ST_Dump(ST_CollectionExtract(
                                ST_Intersection(geometry,
                                    ST_MakeEnvelope(%s, %s, %s, %s, 4326)), 2
                            )) AS part
                        )
                        INSERT INTO pipesets_pipe (pipeset_id, geometry, attributes)
                        SELECT %s, geometry, '{}'::jsonb FROM clipped
                        WHERE ST_Length(geometry::geography) BETWEEN 1 AND 500
                        ORDER BY ST_Length(geometry::geography) DESC LIMIT 1
                        RETURNING id
                        """,
                        [
                            start,
                            min(1, start + length / road_length),
                            road_id,
                            *pipeset.bbox,
                            pipeset.pk,
                        ],
                    )
                    if cursor.fetchone():
                        break
                else:
                    raise ValueError(
                        "Could not generate a pipe between 1 and 500 metres."
                    )

            cursor.execute("DROP TABLE pipe_roads")
            pipeset.status = Pipeset.Status.COMPLETED
            pipeset.save(update_fields=["status"])
    except Exception:
        Pipeset.objects.filter(pk=pipeset_id).update(status=Pipeset.Status.FAILED)
        raise
