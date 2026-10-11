import random
import string
from itertools import batched

from celery import shared_task
from django.db import connection, transaction

from .models import Pipe, Pipeset


def generate_attributes(definitions):
    attributes = {}
    for field in definitions:
        match field["type"]:
            case "string":
                length = random.randint(field["min"], field["max"])
                value = "".join(
                    random.choices(string.ascii_letters + string.digits, k=length)
                )
            case "number":
                value = random.randint(field["min"], field["max"])
            case "boolean":
                value = random.choice((True, False))
            case "category":
                value = random.choice(field["categories"])
            case _:
                raise ValueError("Unknown attribute type.")
        attributes[field["name"]] = value
    return attributes


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

            if pipeset.attribute_definitions:
                pipes = pipeset.pipes.only("id", "attributes").iterator(chunk_size=1000)
                for batch in batched(pipes, 1000):
                    for pipe in batch:
                        pipe.attributes = generate_attributes(
                            pipeset.attribute_definitions
                        )
                    Pipe.objects.bulk_update(batch, ["attributes"], batch_size=1000)

            pipeset.status = Pipeset.Status.COMPLETED
            pipeset.save(update_fields=["status"])
    except Exception:
        Pipeset.objects.filter(pk=pipeset_id).update(status=Pipeset.Status.FAILED)
        raise
