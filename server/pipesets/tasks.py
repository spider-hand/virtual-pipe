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
            # Cut off the parts of each road outside the bbox.
            # Save each remaining line as one pipe, with no length limit.
            cursor.execute(
                """
                INSERT INTO pipesets_pipe (pipeset_id, geometry, attributes)
                SELECT %s, part.geom, '{}'::jsonb
                FROM osm_roads
                CROSS JOIN LATERAL ST_Dump(ST_CollectionExtract(
                    ST_Intersection(geometry, ST_MakeEnvelope(%s, %s, %s, %s, 4326)), 2
                )) AS part
                WHERE geometry && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                    AND ST_Length(part.geom) > 0
                """,
                [pipeset.pk, *pipeset.bbox, *pipeset.bbox],
            )
            if not cursor.rowcount:
                raise ValueError("No roads within the bbox.")

            pipeset.status = Pipeset.Status.COMPLETED
            pipeset.save(update_fields=["status"])
    except Exception:
        Pipeset.objects.filter(pk=pipeset_id).update(status=Pipeset.Status.FAILED)
        raise
