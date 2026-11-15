from uuid import uuid4

import pytest

from pipesets.models import PipeSet

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("status", [PipeSet.Status.PENDING, PipeSet.Status.SUCCEEDED])
def test_get_pipeset_status_returns_current_state_without_caching(client, status):
    pipeset = PipeSet.objects.create(name="Mains", status=status)

    response = client.get(f"/api/pipesets/{pipeset.id}/")

    assert response.status_code == 200
    assert response.json() == {"id": str(pipeset.id), "status": status}
    assert "no-store" in response.headers["Cache-Control"]


def test_get_pipeset_status_includes_the_generation_failure_reason(client):
    pipeset = PipeSet.objects.create(
        name="Mains", status=PipeSet.Status.FAILED, failure_reason="No roads."
    )

    response = client.get(f"/api/pipesets/{pipeset.id}/")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(pipeset.id),
        "status": "failed",
        "failure_reason": "No roads.",
    }
    assert "no-store" in response.headers["Cache-Control"]


def test_get_pipeset_status_returns_not_found_for_an_unknown_id(client):
    response = client.get(f"/api/pipesets/{uuid4()}/")

    assert response.status_code == 404
    assert "no-store" in response.headers["Cache-Control"]
