import io
import subprocess

import pytest
from django.db import IntegrityError, connection
from kombu.exceptions import OperationalError

from pipesets import road_data
from pipesets.models import RoadDataSetup
from pipesets.tasks import prepare_road_data


def test_download_preserves_cached_extract_when_checksum_does_not_match(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)
    cached = tmp_path / "shikoku.osm.pbf"
    cached.write_bytes(b"previous extract")
    extract = io.BytesIO(b"broken extract")
    extract.url = "https://download.geofabrik.de/shikoku.osm.pbf"
    responses = iter([extract, io.BytesIO(b"wrong-checksum")])
    monkeypatch.setattr(road_data, "urlopen", lambda *_args, **_kwargs: next(responses))

    with pytest.raises(ValueError, match="Checksum verification failed"):
        road_data.download_roads("shikoku")

    assert cached.read_bytes() == b"previous extract"
    assert list(tmp_path.iterdir()) == [cached]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("table_exists", "comment", "active_region"),
    [(False, None, None), (True, None, None), (True, "shikoku", "shikoku")],
    ids=["missing", "legacy", "known"],
)
def test_road_data_reports_current_coverage(
    client, tmp_path, monkeypatch, table_exists, comment, active_region
):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)

    if table_exists:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS osm")
            cursor.execute("CREATE TABLE osm.roads (osm_id bigint)")
            if comment:
                cursor.execute("COMMENT ON TABLE osm.roads IS 'shikoku'")

    response = client.get("/api/road-data/")

    assert response.status_code == 200
    assert response.json() == {
        "has_roads": table_exists,
        "active_region": active_region,
        "regions": list(road_data.REGIONS),
        "cached_regions": [],
        "setup": None,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "unusable_import",
    ["empty", "duplicate_ids", "importer_failure"],
)
def test_failed_import_preserves_active_roads_and_region(
    monkeypatch, tmp_path, unusable_import
):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)
    (tmp_path / "kanto.osm.pbf").write_bytes(b"extract")
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS osm")
        cursor.execute("CREATE TABLE osm.roads (osm_id bigint PRIMARY KEY)")
        cursor.execute("INSERT INTO osm.roads VALUES (21)")
        cursor.execute("COMMENT ON TABLE osm.roads IS 'shikoku'")

    def import_extract(*_args, **_kwargs):
        if unusable_import == "importer_failure":
            raise subprocess.CalledProcessError(1, "osm2pgsql")

        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE osm_import.roads (osm_id bigint)")
            if unusable_import == "duplicate_ids":
                cursor.execute("INSERT INTO osm_import.roads VALUES (1), (1)")

    monkeypatch.setattr(road_data.subprocess, "run", import_extract)

    with pytest.raises((ValueError, IntegrityError, subprocess.CalledProcessError)):
        road_data.import_roads("kanto")

    assert road_data.get_coverage() == {"has_roads": True, "active_region": "shikoku"}
    with connection.cursor() as cursor:
        cursor.execute("SELECT osm_id FROM osm.roads")
        assert cursor.fetchall() == [(21,)]


@pytest.mark.django_db
def test_setup_rejects_unsupported_region(client):
    response = client.post("/api/road-data/setups/", {"region": "../osaka"})

    assert response.status_code == 400
    assert not RoadDataSetup.objects.exists()


@pytest.mark.django_db
def test_setup_accepts_only_one_region_at_a_time(client, monkeypatch):
    queued = []
    monkeypatch.setattr(
        prepare_road_data, "apply_async", lambda args, **kwargs: queued.extend(args)
    )

    first = client.post("/api/road-data/setups/", {"region": "shikoku"})
    second = client.post("/api/road-data/setups/", {"region": "kanto"})

    assert first.status_code == 202
    assert first.json()["status"] == "queued"
    assert second.status_code == 409
    assert queued == [first.json()["id"]]


@pytest.mark.django_db
def test_setup_can_be_retried_after_queue_failure(client, monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise OperationalError("unavailable")

    monkeypatch.setattr(prepare_road_data, "apply_async", unavailable)
    response = client.post("/api/road-data/setups/", {"region": "shikoku"})

    assert response.status_code == 503
    job = client.get("/api/road-data/").json()["setup"]
    assert (job["status"], job["failure"]) == ("failed", "queue")

    monkeypatch.setattr(prepare_road_data, "apply_async", lambda **kwargs: None)
    assert (
        client.post("/api/road-data/setups/", {"region": "shikoku"}).status_code == 202
    )


@pytest.mark.django_db
def test_download_failure_prevents_import(client, monkeypatch, tmp_path):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)
    setup = RoadDataSetup.objects.create(region="kanto")

    def download_fails(_region):
        raise OSError("unavailable")

    def unexpected_import(_region):
        pytest.fail("Import should be skipped after download fails")

    monkeypatch.setattr("pipesets.tasks.download_roads", download_fails)
    monkeypatch.setattr("pipesets.tasks.import_roads", unexpected_import)

    prepare_road_data.run(setup.pk)

    job = client.get("/api/road-data/").json()["setup"]
    assert (job["status"], job["failure"]) == ("failed", "download")


@pytest.mark.django_db
def test_road_data_lists_only_complete_cached_extracts(client, monkeypatch, tmp_path):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)
    (tmp_path / "shikoku.osm.pbf").write_bytes(b"extract")
    (tmp_path / "kanto.osm.pbf").touch()
    (tmp_path / "tohoku.osm.pbf.partial").write_bytes(b"partial")

    assert client.get("/api/road-data/").json()["cached_regions"] == ["shikoku"]


@pytest.mark.django_db
def test_setup_rejects_the_already_active_region(client):
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS osm")
        cursor.execute("CREATE TABLE osm.roads (osm_id bigint)")
        cursor.execute("COMMENT ON TABLE osm.roads IS 'shikoku'")

    response = client.post("/api/road-data/setups/", {"region": "shikoku"})

    assert response.status_code == 409
    assert not RoadDataSetup.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cached_bytes", "expected_phases"),
    [
        (b"extract", ["importing"]),
        (None, ["downloading", "importing"]),
        (b"", ["downloading", "importing"]),
    ],
    ids=["cached", "missing", "empty"],
)
def test_setup_downloads_only_when_the_extract_is_missing_or_empty(
    monkeypatch, tmp_path, cached_bytes, expected_phases
):
    monkeypatch.setattr(road_data, "DOWNLOADS", tmp_path)
    setup = RoadDataSetup.objects.create(region="kanto")
    path = tmp_path / "kanto.osm.pbf"
    if cached_bytes is not None:
        path.write_bytes(cached_bytes)

    phases = []

    def download(region):
        setup.refresh_from_db()
        phases.append(setup.status)
        assert region == "kanto"
        path.write_bytes(b"extract")

    def import_extract(region):
        setup.refresh_from_db()
        phases.append(setup.status)
        assert region == "kanto"
        assert path.read_bytes() == b"extract"

    monkeypatch.setattr("pipesets.tasks.download_roads", download)
    monkeypatch.setattr("pipesets.tasks.import_roads", import_extract)
    prepare_road_data.run(setup.pk)

    setup.refresh_from_db()
    assert (setup.status, phases) == ("succeeded", expected_phases)
