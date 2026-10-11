from unittest.mock import patch

import pytest
from django.contrib.gis.geos import LineString
from rest_framework.test import APIClient

from pipesets.models import Pipe, Pipeset

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enqueue():
    with patch("pipesets.views.generate_pipes.delay") as job:
        yield job


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def payload():
    return {"name": "Tokyo pipes", "bbox": [139, 35, 140, 36]}


def test_returns_validated_pipeset(
    client, payload, enqueue, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 202
    assert response.json() == {
        **payload,
        "attribute_definitions": [],
        "id": response.json()["id"],
        "status": "pending",
        "count": 0,
    }

    pipeset = Pipeset.objects.get(pk=response.json()["id"])
    assert pipeset.name == payload["name"]
    assert pipeset.bbox == payload["bbox"]
    assert pipeset.status == "pending"
    enqueue.assert_called_once_with(pipeset.pk)


def test_trims_name(client, payload):
    payload["name"] = "  Tokyo pipes  "

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 202
    assert response.json()["name"] == "Tokyo pipes"


@pytest.mark.parametrize("field", ["name", "bbox"])
def test_rejects_missing_field(client, payload, field):
    del payload[field]

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 400
    assert field in response.json()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("name", "", id="name-empty"),
        pytest.param("name", "   ", id="name-whitespace-only"),
        pytest.param("name", None, id="name-null"),
        pytest.param("name", {}, id="name-object"),
        pytest.param("bbox", None, id="bbox-null"),
        pytest.param("bbox", [], id="bbox-empty"),
        pytest.param("bbox", [139, 35, 140], id="bbox-too-few-coordinates"),
        pytest.param("bbox", [139, 35, 140, 36, 37], id="bbox-too-many-coordinates"),
        pytest.param(
            "bbox", ["invalid", 35, 140, 36], id="bbox-non-numeric-coordinate"
        ),
        pytest.param("bbox", ["NaN", 35, 140, 36], id="bbox-nan-coordinate"),
        pytest.param("bbox", [139, 35, "Infinity", 36], id="bbox-infinite-coordinate"),
        pytest.param("bbox", [-181, 35, 140, 36], id="bbox-west-below-minimum"),
        pytest.param("bbox", [139, 35, 181, 36], id="bbox-east-above-maximum"),
        pytest.param("bbox", [139, -91, 140, 36], id="bbox-south-below-minimum"),
        pytest.param("bbox", [139, 35, 140, 91], id="bbox-north-above-maximum"),
        pytest.param("bbox", [140, 35, 139, 36], id="bbox-west-greater-than-east"),
        pytest.param("bbox", [139, 36, 140, 35], id="bbox-south-greater-than-north"),
        pytest.param("bbox", [139, 35, 139, 36], id="bbox-zero-width"),
        pytest.param("bbox", [139, 35, 140, 35], id="bbox-zero-height"),
    ],
)
def test_rejects_invalid_field(client, payload, field, value):
    payload[field] = value

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 400
    assert field in response.json()


def test_accepts_coordinate_boundaries(client, payload):
    payload.update(bbox=[-180, -90, 180, 90])

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 202
    assert response.json() == {
        **payload,
        "attribute_definitions": [],
        "id": response.json()["id"],
        "status": "pending",
        "count": 0,
    }


@pytest.mark.parametrize("status", ["pending", "failed", "completed"])
def test_gets_pipeset(client, payload, status):
    pipeset = Pipeset.objects.create(**payload, status=status)
    if status == "completed":
        Pipe.objects.create(
            pipeset=pipeset,
            geometry=LineString((139, 35), (140, 36), srid=4326),
        )
    response = client.get(f"/pipesets/{pipeset.pk}")
    assert response.status_code == 200
    assert response.json() == {
        **payload,
        "attribute_definitions": [],
        "id": pipeset.pk,
        "status": status,
        "count": 1 if status == "completed" else 0,
    }


def test_returns_not_found(client):
    response = client.get("/pipesets/999999")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.django_db(transaction=True)
def test_marks_failed_when_enqueue_fails(client, payload, enqueue):
    enqueue.side_effect = RuntimeError("Broker unavailable")
    response = client.post("/pipesets", payload, format="json")
    assert response.status_code == 503
    assert response.json() == {"detail": "Failed to enqueue pipeset generation."}
    assert Pipeset.objects.get().status == "failed"


def test_persists_normalized_attribute_definitions(client, payload):
    payload["attribute_definitions"] = [
        {"name": " label ", "type": "string", "min": 0, "max": 8},
        {"name": "diameter", "type": "number", "min": -10, "max": 10},
        {"name": "active", "type": "boolean"},
        {
            "name": "material",
            "type": "category",
            "categories": [" PVC ", "", "PVC", "steel"],
        },
    ]
    response = client.post("/pipesets", payload, format="json")
    assert response.status_code == 202
    definitions = response.json()["attribute_definitions"]
    assert definitions[0]["name"] == "label"
    assert definitions[3]["categories"] == ["PVC", "steel"]
    assert Pipeset.objects.get().attribute_definitions == definitions
    assert (
        client.get(f"/pipesets/{response.json()['id']}").json()["attribute_definitions"]
        == definitions
    )


@pytest.mark.parametrize(
    "definitions",
    [
        pytest.param(None, id="invalid-definitions-null"),
        pytest.param({}, id="invalid-definitions-not-list"),
        pytest.param([{"name": "", "type": "boolean"}], id="invalid-name-empty"),
        pytest.param(
            [{"name": "id", "type": "boolean"}], id="invalid-name-reserved-id"
        ),
        pytest.param(
            [{"name": "pipeset_id", "type": "boolean"}],
            id="invalid-name-reserved-pipeset-id",
        ),
        pytest.param(
            [{"name": "geometry", "type": "boolean"}],
            id="invalid-name-reserved-geometry",
        ),
        pytest.param(
            [{"name": "a", "type": "boolean"}, {"name": " a ", "type": "boolean"}],
            id="invalid-name-duplicate-after-trimming",
        ),
        pytest.param([{"name": "a", "type": "invalid"}], id="invalid-type-unsupported"),
        pytest.param(
            [{"name": "a", "type": "string", "min": -1, "max": 2}],
            id="invalid-string-negative-length",
        ),
        pytest.param(
            [{"name": "a", "type": "string", "min": 3, "max": 2}],
            id="invalid-string-min-exceeds-max",
        ),
        pytest.param(
            [{"name": "a", "type": "number", "min": 0.5, "max": 2}],
            id="invalid-number-fractional-bound",
        ),
        pytest.param(
            [{"name": "a", "type": "number", "min": 0}], id="invalid-number-max-missing"
        ),
        pytest.param(
            [{"name": "a", "type": "number", "min": 0, "max": 2**53}],
            id="invalid-number-exceeds-safe-integer",
        ),
        pytest.param(
            [{"name": "a", "type": "category", "categories": []}],
            id="invalid-category-no-options",
        ),
        pytest.param(
            [{"name": "a", "type": "category", "categories": [" ", ""]}],
            id="invalid-category-only-blank-options",
        ),
    ],
)
def test_rejects_invalid_attribute_definitions(client, payload, definitions, enqueue):
    payload["attribute_definitions"] = definitions
    response = client.post("/pipesets", payload, format="json")
    assert response.status_code == 400
    assert "attribute_definitions" in response.json()
    assert not Pipeset.objects.exists()
    enqueue.assert_not_called()
