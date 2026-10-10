from celery import shared_task

from .models import Pipeset


@shared_task(ignore_result=True)
def generate_pipes(pipeset_id):
    try:
        pipeset = Pipeset.objects.get(pk=pipeset_id)
        pipeset.status = Pipeset.Status.COMPLETED
        pipeset.save(update_fields=["status"])
    except Exception:
        Pipeset.objects.filter(pk=pipeset_id).update(status=Pipeset.Status.FAILED)
        raise
