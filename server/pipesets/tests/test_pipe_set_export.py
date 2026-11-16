import csv
from datetime import date
from decimal import Decimal
from email.message import Message
from io import StringIO
from uuid import uuid4

import duckdb
import pytest
from django.contrib.gis.geos import LineString
from django.urls import reverse

from pipesets.models.pipeset import AttributeSet, Pipe, PipeSet

pytestmark = pytest.mark.django_db
GEOMETRY = LineString((139, 35), (140, 36), srid=4326)
WKT = "LINESTRING(139 35,140 36)"
DECIMAL = "0.123456789012345678901234567890"
WIDE_DECIMAL = "0.123456789012345678901234567890123456789"
WIDE_INTEGER = 2**70


@pytest.fixture
def pipeset():
    definitions = [
        {"name": "material", "type": "string", "choices": ['鋼, "lining"']},
        {"name": "diameter", "type": "integer", "min": "0", "max": "100"},
        {"name": "pressure", "type": "decimal", "min": DECIMAL, "max": DECIMAL},
        {"name": "active", "type": "boolean"},
        {"name": "installed", "type": "date", "min": "2025-01-01", "max": "2025-01-02"},
        {"name": "pipe_id", "type": "id", "id_format": "sequential"},
        {
            "name": "wide_integer",
            "type": "integer",
            "min": "0",
            "max": str(WIDE_INTEGER),
        },
        {
            "name": "wide_decimal",
            "type": "decimal",
            "min": WIDE_DECIMAL,
            "max": WIDE_DECIMAL,
        },
    ]
    attribute_set = AttributeSet.objects.create(name="Custom", attributes=definitions)
    pipeset = PipeSet.objects.create(name="東京 mains", attribute_set=attribute_set)
    Pipe.objects.create(
        pipeset=pipeset,
        geometry=GEOMETRY,
        attributes={
            "material": '鋼, "lining"',
            "diameter": 75,
            "pressure": DECIMAL,
            "active": False,
            "installed": "2025-01-02",
            "pipe_id": "PIPE-000001",
            "wide_integer": WIDE_INTEGER,
            "wide_decimal": WIDE_DECIMAL,
            "unconfigured": "excluded",
        },
    )
    Pipe.objects.create(pipeset=pipeset, geometry=GEOMETRY, attributes={"diameter": 80})
    unrelated = PipeSet.objects.create(name="Unrelated")
    Pipe.objects.create(pipeset=unrelated, geometry=GEOMETRY)
    return pipeset


def export_url(pipeset_id):
    return reverse("pipeset-export", kwargs={"id": pipeset_id})


def test_export_csv_writes_only_configured_attributes_and_wkt(client, pipeset):
    response = client.get(export_url(pipeset.pk), {"file_format": "csv"})

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    content = b"".join(response.streaming_content).decode("utf-8")
    rows = list(csv.reader(StringIO(content)))
    assert rows == [
        [*(rule["name"] for rule in pipeset.attribute_set.attributes), "geometry"],
        [
            '鋼, "lining"',
            "75",
            DECIMAL,
            "False",
            "2025-01-02",
            "PIPE-000001",
            str(WIDE_INTEGER),
            WIDE_DECIMAL,
            WKT,
        ],
        ["", "80", "", "", "", "", "", "", WKT],
    ]


def test_export_parquet_preserves_native_types_and_wide_numbers(
    client, pipeset, tmp_path
):
    response = client.get(export_url(pipeset.pk), {"file_format": "parquet"})

    assert response.status_code == 200
    assert response["Content-Type"] == "application/vnd.apache.parquet"
    file = tmp_path / "download.parquet"
    file.write_bytes(b"".join(response.streaming_content))
    with duckdb.connect() as connection:
        result = connection.read_parquet(str(file))
        assert result.columns == [
            *(rule["name"] for rule in pipeset.attribute_set.attributes),
            "geometry",
        ]
        assert [str(column_type) for column_type in result.types] == [
            "VARCHAR",
            "BIGINT",
            "DECIMAL(30,30)",
            "BOOLEAN",
            "DATE",
            "VARCHAR",
            "VARCHAR",
            "VARCHAR",
            "VARCHAR",
        ]
        assert result.fetchall() == [
            (
                '鋼, "lining"',
                75,
                Decimal(DECIMAL),
                False,
                date(2025, 1, 2),
                "PIPE-000001",
                str(WIDE_INTEGER),
                WIDE_DECIMAL,
                WKT,
            ),
            (None, 80, None, None, None, None, None, None, WKT),
        ]


@pytest.mark.parametrize("file_format", ["csv", "parquet"])
def test_export_uses_the_saved_name_in_the_attachment_header(client, file_format):
    pipeset = PipeSet.objects.create(name="東京 mains/a\\b\t")

    response = client.get(export_url(pipeset.pk), {"file_format": file_format})

    assert response.status_code == 200
    headers = Message()
    headers["Content-Disposition"] = response["Content-Disposition"]
    assert headers.get_filename() == f"東京 mains_a_b_.{file_format}"
    response.close()


@pytest.mark.parametrize("file_format", ["csv", "parquet"])
def test_export_empty_set_retains_its_defined_columns(client, tmp_path, file_format):
    attribute_set = AttributeSet.objects.create(
        name="Custom", attributes=[{"name": "active", "type": "boolean"}]
    )
    pipeset = PipeSet.objects.create(name="Empty", attribute_set=attribute_set)

    response = client.get(export_url(pipeset.pk), {"file_format": file_format})

    assert response.status_code == 200
    content = b"".join(response.streaming_content)
    if file_format == "csv":
        assert list(csv.reader(StringIO(content.decode()))) == [["active", "geometry"]]
    else:
        file = tmp_path / "empty.parquet"
        file.write_bytes(content)
        with duckdb.connect() as connection:
            result = connection.read_parquet(str(file))
            assert result.columns == ["active", "geometry"]
            assert result.fetchall() == []


def test_export_without_definitions_contains_only_geometry(client):
    pipeset = PipeSet.objects.create(name="Geometry only")
    Pipe.objects.create(pipeset=pipeset, geometry=GEOMETRY, attributes={"ignored": 1})

    response = client.get(export_url(pipeset.pk), {"file_format": "csv"})

    assert response.status_code == 200
    content = b"".join(response.streaming_content).decode()
    assert list(csv.reader(StringIO(content))) == [["geometry"], [WKT]]


@pytest.mark.parametrize("params", [{}, {"file_format": "json"}])
def test_export_requires_a_supported_file_format(client, params):
    pipeset = PipeSet.objects.create(name="Mains")

    assert client.get(export_url(pipeset.pk), params).status_code == 400


def test_export_returns_not_found_for_an_unknown_set(client):
    assert client.get(export_url(uuid4()), {"file_format": "csv"}).status_code == 404


@pytest.mark.parametrize("status", [PipeSet.Status.PENDING, PipeSet.Status.FAILED])
def test_export_rejects_sets_that_did_not_finish_successfully(client, status):
    pipeset = PipeSet.objects.create(name="Mains", status=status)

    assert client.get(export_url(pipeset.pk), {"file_format": "csv"}).status_code == 409


def test_export_rejects_an_existing_conflicting_geometry_definition(client):
    attribute_set = AttributeSet.objects.create(
        name="Custom", attributes=[{"name": "geometry", "type": "boolean"}]
    )
    pipeset = PipeSet.objects.create(name="Mains", attribute_set=attribute_set)

    assert client.get(export_url(pipeset.pk), {"file_format": "csv"}).status_code == 409
