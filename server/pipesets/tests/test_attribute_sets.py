from uuid import UUID

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from pipesets.models import AttributeSet

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_list_attribute_sets_returns_an_empty_array_when_no_sets_are_saved(client):
    response = client.get(reverse("attribute-sets"))

    assert response.status_code == 200
    assert response.data == []


def test_list_attribute_sets_returns_complete_sets_ordered_by_name_then_id(client):
    attributes = [
        {"name": "material", "type": "string", "choices": ["PVC", "鋼"]},
        {"name": "pressure", "type": "decimal", "min": "1.20", "max": "2.00"},
        {"name": "pipe_id", "type": "id", "id_format": "uuid"},
    ]
    later_id = UUID(int=2)
    earlier_id = UUID(int=1)
    last_id = UUID(int=3)
    AttributeSet.objects.create(id=last_id, name="Services", attributes=attributes)
    AttributeSet.objects.create(id=later_id, name="Mains", attributes=attributes)
    AttributeSet.objects.create(id=earlier_id, name="Mains", attributes=attributes)

    response = client.get(reverse("attribute-sets"))

    assert response.status_code == 200
    assert response.data == [
        {"id": str(earlier_id), "name": "Mains", "attributes": attributes},
        {"id": str(later_id), "name": "Mains", "attributes": attributes},
        {"id": str(last_id), "name": "Services", "attributes": attributes},
    ]


def test_create_attribute_set_preserves_order_and_bounds(client):
    attributes = [
        {"name": "material", "type": "string", "choices": ["PVC", "鋼"]},
        {"name": "pressure", "type": "decimal", "min": "1.20", "max": "2.00"},
        {"name": "diameter", "type": "integer", "min": "-1", "max": "-1"},
        {"name": "active", "type": "boolean"},
        {"name": "installed", "type": "date", "min": "2024-02-29", "max": "2024-03-01"},
        {"name": "pipe_id", "type": "id", "id_format": "uuid"},
    ]

    response = client.post(
        reverse("attribute-sets"),
        {"name": " 配水管 ", "attributes": attributes},
        format="json",
    )

    assert response.status_code == 201
    saved = AttributeSet.objects.get(id=UUID(response.data["id"]))
    assert saved.name == "配水管"
    assert saved.attributes == attributes
    assert response.data["attributes"] == attributes


def test_create_attribute_set_allows_repeated_display_names(client):
    payload = {"name": "Mains", "attributes": [{"name": "active", "type": "boolean"}]}

    first = client.post(reverse("attribute-sets"), payload, format="json")
    second = client.post(reverse("attribute-sets"), payload, format="json")

    assert first.status_code == second.status_code == 201
    assert first.data["id"] != second.data["id"]


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(" ", id="blank_display_name"),
        pytest.param("a" * 256, id="display_name_exceeds_255_characters"),
    ],
)
def test_create_attribute_set_rejects_invalid_display_names(client, name):
    response = client.post(
        reverse("attribute-sets"),
        {"name": name, "attributes": [{"name": "active", "type": "boolean"}]},
        format="json",
    )

    assert response.status_code == 400
    assert not AttributeSet.objects.exists()


@pytest.mark.parametrize(
    "attributes",
    [
        pytest.param(
            [],
            id="no_attributes",
        ),
        pytest.param(
            [{"name": "管径", "type": "boolean"}],
            id="non_ascii_field_name",
        ),
        pytest.param(
            [
                {"name": "active", "type": "boolean"},
                {"name": " active ", "type": "id", "id_format": "uuid"},
            ],
            id="duplicate_field_names_after_trimming",
        ),
        pytest.param(
            [{"name": "material", "type": "string", "choices": [" "]}],
            id="blank_string_choice",
        ),
        pytest.param(
            [{"name": "material", "type": "string", "choices": []}],
            id="no_string_choices",
        ),
        pytest.param(
            [{"name": "material", "type": "string", "choices": [1]}],
            id="non_string_choice",
        ),
        pytest.param(
            [{"name": "diameter", "type": "integer", "min": "-5", "max": "-9"}],
            id="reversed_integer_bounds",
        ),
        pytest.param(
            [{"name": "diameter", "type": "integer", "min": "1.2", "max": "2"}],
            id="fractional_integer_bound",
        ),
        pytest.param(
            [{"name": "diameter", "type": "integer", "min": 1, "max": 2}],
            id="integer_bounds_are_json_numbers",
        ),
        pytest.param(
            [{"name": "pressure", "type": "decimal", "min": "1.2", "max": "2.00"}],
            id="mismatched_decimal_precision",
        ),
        pytest.param(
            [{"name": "pressure", "type": "decimal", "min": "2.01", "max": "2.00"}],
            id="reversed_decimal_bounds",
        ),
        pytest.param(
            [
                {
                    "name": "installed",
                    "type": "date",
                    "min": "2023-02-29",
                    "max": "2024-03-01",
                }
            ],
            id="invalid_calendar_date",
        ),
        pytest.param(
            [{"name": "pipe_id", "type": "id", "id_format": "random"}],
            id="unsupported_id_format",
        ),
        pytest.param(
            [{"name": "active", "type": []}],
            id="attribute_type_is_a_list",
        ),
        pytest.param(
            [{"name": "active", "type": "unknown"}],
            id="unknown_attribute_type",
        ),
    ],
)
def test_create_attribute_set_rejects_invalid_definitions(client, attributes):
    response = client.post(
        reverse("attribute-sets"),
        {"name": "Mains", "attributes": attributes},
        format="json",
    )

    assert response.status_code == 400
    assert not AttributeSet.objects.exists()


def test_create_attribute_set_rejects_the_reserved_geometry_name(client):
    response = client.post(
        reverse("attribute-sets"),
        {"name": "Mains", "attributes": [{"name": "geometry", "type": "boolean"}]},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["attributes"][0]["name"] == [
        "The geometry column is reserved."
    ]
    assert not AttributeSet.objects.exists()
