from unittest.mock import patch

import pytest

from pipesets.models import Pipeset
from pipesets.tasks import generate_pipes

pytestmark = pytest.mark.django_db


@pytest.fixture
def pipeset():
    return Pipeset.objects.create(name="Tokyo pipes", count=25, bbox=[139, 35, 140, 36])


def test_completes_pipeset(pipeset):
    generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "completed"


def test_marks_failed_and_raises(pipeset):
    with (
        patch.object(Pipeset, "save", side_effect=RuntimeError("Processing failed")),
        pytest.raises(RuntimeError, match="Processing failed"),
    ):
        generate_pipes(pipeset.pk)
    pipeset.refresh_from_db()
    assert pipeset.status == "failed"
