import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def payload():
    return {"name": "Tokyo pipes", "count": 25, "bbox": [139, 35, 140, 36]}


def test_returns_validated_pipeset(client, payload):
    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 200
    assert response.json() == payload


def test_trims_name(client, payload):
    payload["name"] = "  Tokyo pipes  "

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 200
    assert response.json()["name"] == "Tokyo pipes"


@pytest.mark.parametrize("field", ["name", "count", "bbox"])
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
        pytest.param("count", 0, id="count-zero"),
        pytest.param("count", -1, id="count-negative"),
        pytest.param("count", 1.5, id="count-fractional"),
        pytest.param("count", "", id="count-empty"),
        pytest.param("count", None, id="count-null"),
        pytest.param("count", True, id="count-boolean"),
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


def test_accepts_coordinate_boundaries_and_count_one(client, payload):
    payload.update(count=1, bbox=[-180, -90, 180, 90])

    response = client.post("/pipesets", payload, format="json")

    assert response.status_code == 200
    assert response.json() == payload
