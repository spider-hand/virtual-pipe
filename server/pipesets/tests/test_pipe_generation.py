from uuid import UUID, uuid4

import duckdb
import pytest
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from django.db.models import ProtectedError
from kombu.exceptions import OperationalError

from pipesets.models import AttributeSet, Pipe, PipeSet
from pipesets.tasks import generate_attribute, generate_pipeset

DISTRICT_ID = "01234"
DISTRICT_LABEL = "Sample Municipality"
BOUNDARY = (
    "MULTIPOLYGON(((0 0, 6 0, 6 6, 0 6, 0 0),"
    "(2 2, 2 4, 4 4, 4 2, 2 2)),"
    "((8 0, 10 0, 10 6, 8 6, 8 0)))"
)
SEQUENCE = {"name": "pipe_id", "type": "id", "id_format": "sequential"}
RULES = [SEQUENCE, {"name": "material", "type": "string", "choices": ["PVC"]}]


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    path = tmp_path / "districts.duckdb"
    monkeypatch.setattr("pipesets.district_catalog.CATALOG", path)

    with duckdb.connect(str(path)) as catalog:
        catalog.execute(
            "CREATE TABLE districts (code VARCHAR, label VARCHAR, boundary_wkb BLOB)"
        )
        catalog.execute(
            "INSERT INTO districts VALUES (?, ?, ?)",
            [DISTRICT_ID, DISTRICT_LABEL, bytes(GEOSGeometry(BOUNDARY).wkb)],
        )

    return path


@pytest.fixture
def attribute_set(db):
    return AttributeSet.objects.create(name="Mains", attributes=RULES)


@pytest.fixture
def pending_set(catalog, attribute_set):
    return PipeSet.objects.create(
        name="Test pipes",
        district_id=DISTRICT_ID,
        attribute_set=attribute_set,
        status=PipeSet.Status.PENDING,
    )


@pytest.fixture
def roads(db):
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS osm")
        cursor.execute(
            "CREATE TABLE osm.roads "
            "(osm_id bigint PRIMARY KEY, geom geometry(LineString, 4326))"
        )
        cursor.execute("CREATE INDEX ON osm.roads USING gist (geom)")

    def add(road_id, line):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO osm.roads VALUES (%s, ST_GeomFromText(%s, 4326))",
                [road_id, line],
            )

    return add


@pytest.mark.django_db(transaction=True)
def test_create_pipeset_commits_the_pending_set_before_publishing(
    client, catalog, attribute_set, monkeypatch
):
    published = []

    def publish(*, args, retry):
        assert not connection.in_atomic_block
        assert retry is False
        pipe_set = PipeSet.objects.get(pk=args[0])
        assert pipe_set.status == PipeSet.Status.PENDING
        published.append(args[0])

    monkeypatch.setattr("pipesets.views.generate_pipeset.apply_async", publish)

    response = client.post(
        "/api/pipesets/",
        {"district_id": DISTRICT_ID, "attribute_set_id": str(attribute_set.id)},
        content_type="application/json",
    )

    assert response.status_code == 202
    assert published == [response.json()["id"]]
    pipe_set = PipeSet.objects.get(pk=published[0])
    assert pipe_set.name == f"{DISTRICT_LABEL} — Mains"
    assert pipe_set.district_id == DISTRICT_ID
    assert pipe_set.attribute_set == attribute_set
    assert not pipe_set.pipe_set.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("district_id", "1234"),
        ("district_id", 12345),
        ("district_id", "0123a"),
        ("attribute_set_id", "bad-id"),
        ("attribute_set_id", 1),
    ],
)
def test_create_pipeset_rejects_malformed_ids(client, field, value):
    payload = {
        "district_id": DISTRICT_ID,
        "attribute_set_id": str(uuid4()),
        field: value,
    }

    response = client.post("/api/pipesets/", payload, content_type="application/json")

    assert response.status_code == 400
    assert field in response.json()
    assert not PipeSet.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("missing", ["district", "attribute_set"])
def test_create_pipeset_returns_not_found_for_unknown_ids(
    client, catalog, attribute_set, missing
):
    district_id = "99999" if missing == "district" else DISTRICT_ID
    attribute_set_id = uuid4() if missing == "attribute_set" else attribute_set.id

    response = client.post(
        "/api/pipesets/",
        {"district_id": district_id, "attribute_set_id": str(attribute_set_id)},
        content_type="application/json",
    )

    assert response.status_code == 404
    assert not PipeSet.objects.exists()


def test_create_pipeset_reports_unavailable_catalog(
    client, attribute_set, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "pipesets.district_catalog.CATALOG", tmp_path / "missing.duckdb"
    )

    response = client.post(
        "/api/pipesets/",
        {"district_id": DISTRICT_ID, "attribute_set_id": str(attribute_set.id)},
        content_type="application/json",
    )

    assert response.status_code == 503
    assert not PipeSet.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_create_pipeset_records_failure_if_the_broker_is_unavailable(
    client, catalog, attribute_set, monkeypatch
):
    def unavailable(**kwargs):
        raise OperationalError("Broker is down")

    monkeypatch.setattr("pipesets.views.generate_pipeset.apply_async", unavailable)

    response = client.post(
        "/api/pipesets/",
        {"district_id": DISTRICT_ID, "attribute_set_id": str(attribute_set.id)},
        content_type="application/json",
    )

    assert response.status_code == 503
    pipe_set = PipeSet.objects.get()
    assert pipe_set.status == PipeSet.Status.FAILED
    assert pipe_set.failure_reason == response.json()["detail"]
    assert not Pipe.objects.exists()


def test_generation_clips_crossing_roads_and_keeps_inside_roads(pending_set, roads):
    roads(20, "LINESTRING(-1 3, 11 3)")
    roads(10, "LINESTRING(1 1, 2 1)")
    roads(30, "LINESTRING(-1 1, 0 0)")
    roads(40, "LINESTRING(2.5 3, 3.5 3)")

    generate_pipeset(str(pending_set.pk))
    generate_pipeset(str(pending_set.pk))

    pending_set.refresh_from_db()
    assert pending_set.status == PipeSet.Status.SUCCEEDED
    pipes = list(Pipe.objects.filter(pipeset=pending_set).order_by("id"))
    assert len(pipes) == 4
    assert pipes[0].geometry.equals(GEOSGeometry("LINESTRING(1 1, 2 1)"))
    assert {pipe.geometry.extent for pipe in pipes[1:]} == {
        (0, 3, 2, 3),
        (4, 3, 6, 3),
        (8, 3, 10, 3),
    }
    assert [pipe.attributes for pipe in pipes] == [
        {"pipe_id": f"PIPE-{sequence:06d}", "material": "PVC"}
        for sequence in range(1, 5)
    ]


def test_generation_fails_when_no_roads_have_been_imported(pending_set):
    generate_pipeset(str(pending_set.pk))

    pending_set.refresh_from_db()
    assert pending_set.status == PipeSet.Status.FAILED
    assert "No OSM roads have been imported" in pending_set.failure_reason
    assert not Pipe.objects.exists()


def test_attribute_set_cannot_be_deleted_while_a_pipeset_references_it(pending_set):
    with pytest.raises(ProtectedError):
        pending_set.attribute_set.delete()


def test_generation_fails_when_the_import_has_no_roads_in_the_district(
    pending_set, roads
):
    roads(1, "LINESTRING(30 30, 31 31)")

    generate_pipeset(str(pending_set.pk))

    pending_set.refresh_from_db()
    assert pending_set.status == PipeSet.Status.FAILED
    assert "no roads within this district" in pending_set.failure_reason
    assert not Pipe.objects.exists()


def test_generation_rolls_back_earlier_batches_if_a_later_insert_fails(
    pending_set, roads, monkeypatch
):
    roads(1, "LINESTRING(1 1, 2 1)")
    roads(2, "LINESTRING(1 2, 2 2)")
    monkeypatch.setattr("pipesets.tasks.BATCH_SIZE", 1)
    bulk_create = Pipe.objects.bulk_create

    def insert(pipes):
        if pipes[0].attributes["pipe_id"] == "PIPE-000002":
            raise ValueError("Insert failed")
        bulk_create(pipes)

    monkeypatch.setattr(Pipe.objects, "bulk_create", insert)

    generate_pipeset(str(pending_set.pk))

    pending_set.refresh_from_db()
    assert pending_set.status == PipeSet.Status.FAILED
    assert pending_set.failure_reason
    assert not Pipe.objects.exists()


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ({"type": "string", "choices": ["鋼"]}, "鋼"),
        ({"type": "boolean"}, True),
        ({"type": "integer", "min": "-2", "max": "3"}, 3),
        ({"type": "integer", "min": "-2", "max": "-2"}, -2),
        ({"type": "decimal", "min": "-2.00", "max": "-1.20"}, "-1.20"),
        ({"type": "decimal", "min": "0.000", "max": "0.000"}, "0.000"),
        ({"type": "date", "min": "2024-02-28", "max": "2024-02-29"}, "2024-02-29"),
        (SEQUENCE, "PIPE-000002"),
    ],
)
def test_generate_attribute_respects_the_rule_and_includes_upper_bounds(
    rule, expected, monkeypatch
):
    monkeypatch.setattr("pipesets.tasks.random.randint", lambda lower, upper: upper)
    monkeypatch.setattr("pipesets.tasks.random.getrandbits", lambda width: 1)

    result = generate_attribute(rule, 2)

    assert result == expected
    assert type(result) is type(expected)


def test_generate_attribute_returns_a_uuid_string():
    rule = {"type": "id", "id_format": "uuid"}

    value = generate_attribute(rule, 1)

    assert UUID(value).version == 4
