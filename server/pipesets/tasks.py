import logging
import random
from datetime import date
from decimal import Decimal
from uuid import uuid4

from celery import shared_task
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, transaction

from pipesets.district_catalog import get_district, get_prefecture
from pipesets.models import Pipe, PipeSet, RoadDataSetup
from pipesets.road_data import download_roads, has_cached_extract, import_roads

logger = logging.getLogger(__name__)
BATCH_SIZE = 1000


class GenerationError(Exception):
    pass


def generate_attribute(rule, sequence):
    match rule["type"]:
        case "string":
            return random.choice(rule["choices"])
        case "boolean":
            return bool(random.getrandbits(1))
        case "integer":
            return random.randint(int(rule["min"]), int(rule["max"]))
        case "decimal":
            scale = len(rule["min"].split(".")[1])
            lower = int(rule["min"].replace(".", ""))
            upper = int(rule["max"].replace(".", ""))
            units = random.randint(lower, upper)
            return format(Decimal(f"{units}e-{scale}"), "f")
        case "date":
            lower = date.fromisoformat(rule["min"]).toordinal()
            upper = date.fromisoformat(rule["max"]).toordinal()
            return date.fromordinal(random.randint(lower, upper)).isoformat()
        case "id":
            return (
                f"PIPE-{sequence:06d}"
                if rule["id_format"] == "sequential"
                else str(uuid4())
            )
        case _:
            raise ValueError(f"Unknown attribute type: {rule['type']}")


def populate_pipes(pipeset):
    if pipeset.attribute_set is None:
        raise GenerationError("The pipe set has no associated attribute set.")

    rules = pipeset.attribute_set.attributes
    if pipeset.prefecture_id:
        area_name = "prefecture"
        area = get_prefecture(pipeset.prefecture_id)
    else:
        area_name = "district"
        area = get_district(pipeset.district_id)

    if area is None:
        raise GenerationError(
            f"The {area_name} is missing from the {area_name} catalog."
        )

    _, boundary = area
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('osm.roads')")
        if cursor.fetchone()[0] is None:
            raise GenerationError("No OSM roads have been imported.")

    sequence = 0
    with connection.chunked_cursor() as cursor:
        cursor.execute(
            """
            WITH area AS (
                SELECT ST_GeomFromWKB(%s, 4326) AS geom
            )
            SELECT ST_AsBinary(segment.geom)
            FROM area
            JOIN osm.roads ON ST_Intersects(roads.geom, area.geom)
            CROSS JOIN LATERAL ST_Dump(
                ST_CollectionExtract(ST_Intersection(roads.geom, area.geom), 2)
            ) AS segment
            WHERE ST_Length(segment.geom) > 0
            ORDER BY roads.osm_id, segment.path
            """,
            [boundary],
        )

        while rows := cursor.fetchmany(BATCH_SIZE):
            pipes = []
            for (geometry,) in rows:
                sequence += 1
                pipes.append(
                    Pipe(
                        pipeset=pipeset,
                        geometry=GEOSGeometry(memoryview(geometry), srid=4326),
                        attributes={
                            rule["name"]: generate_attribute(rule, sequence)
                            for rule in rules
                        },
                    )
                )

            Pipe.objects.bulk_create(pipes)

    if not sequence:
        raise GenerationError(
            f"The active OSM import has no roads within this {area_name}."
        )


@shared_task(acks_late=True, reject_on_worker_lost=True, ignore_result=True)
def prepare_road_data(setup_id):
    status = RoadDataSetup.Status
    failure = RoadDataSetup.Failure
    setup = RoadDataSetup.objects.filter(
        pk=setup_id, status__in=[status.QUEUED, status.DOWNLOADING, status.IMPORTING]
    ).first()
    if setup is None:
        return

    steps = (
        (status.DOWNLOADING, failure.DOWNLOAD, download_roads),
        (status.IMPORTING, failure.IMPORT, import_roads),
    )
    for phase, reason, operation in steps:
        try:
            if phase == status.DOWNLOADING and has_cached_extract(setup.region):
                continue

            setup.status = phase
            setup.save(update_fields=["status"])
            operation(setup.region)
        except Exception:
            logger.exception("Road data setup %s failed during %s", setup_id, phase)
            setup.status = status.FAILED
            setup.failure = reason
            setup.save(update_fields=["status", "failure"])
            return

    setup.status = status.SUCCEEDED
    setup.save(update_fields=["status"])


@shared_task(acks_late=True, reject_on_worker_lost=True, ignore_result=True)
def generate_pipeset(pipeset_id):
    with transaction.atomic():
        pipeset = PipeSet.objects.select_for_update().filter(pk=pipeset_id).first()
        if pipeset is None or pipeset.status != PipeSet.Status.PENDING:
            return

        try:
            with transaction.atomic():
                populate_pipes(pipeset)
        except GenerationError as error:
            pipeset.status = PipeSet.Status.FAILED
            pipeset.failure_reason = str(error)
        except Exception:
            logger.exception("Pipe generation failed for %s", pipeset_id)
            pipeset.status = PipeSet.Status.FAILED
            pipeset.failure_reason = "Pipe generation failed. Check the worker logs."
        else:
            pipeset.status = PipeSet.Status.SUCCEEDED

        pipeset.save(update_fields=["status", "failure_reason"])
