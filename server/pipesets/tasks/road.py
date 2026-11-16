import logging

from celery import shared_task

from pipesets.models.road import RoadDataSetup
from pipesets.road_data import download_roads, has_cached_extract, import_roads

logger = logging.getLogger(__name__)


@shared_task(
    name="pipesets.tasks.prepare_road_data",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
)
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
