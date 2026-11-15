import duckdb
import pytest

from pipesets import district_catalog


@pytest.fixture
def prefecture_catalog(tmp_path, monkeypatch):
    catalog = tmp_path / "areas.duckdb"
    monkeypatch.setattr(district_catalog, "CATALOG", catalog)

    with duckdb.connect(str(catalog)) as connection:
        connection.execute(
            """
            CREATE TABLE prefectures (
                code VARCHAR, label VARCHAR, label_en VARCHAR, bounds DOUBLE[]
            )
            """
        )
        connection.executemany(
            "INSERT INTO prefectures VALUES (?, ?, ?, [130, 31, 131, 32])",
            [
                (
                    f"{i:02d}",
                    "北海道" if i == 1 else f"試験県 {i}",
                    "Hokkaido" if i == 1 else None,
                )
                for i in range(47, 0, -1)
            ],
        )

    return catalog


def test_list_returns_all_prefectures_in_code_order(client, prefecture_catalog):
    response = client.get("/api/prefectures/")

    assert response.status_code == 200
    entries = response.json()
    assert [entry["code"] for entry in entries] == [f"{i:02d}" for i in range(1, 48)]
    assert entries[0] == {
        "code": "01",
        "label": "北海道",
        "label_en": "Hokkaido",
        "bounds": [130, 31, 131, 32],
    }


@pytest.mark.parametrize("unavailable", ["missing", "unreadable"])
def test_list_reports_an_unavailable_catalog(
    client, tmp_path, monkeypatch, unavailable
):
    catalog = tmp_path / "areas.duckdb"
    monkeypatch.setattr(district_catalog, "CATALOG", catalog)
    if unavailable == "unreadable":
        catalog.write_text("not a DuckDB database")

    response = client.get("/api/prefectures/")

    assert response.status_code == 503
    assert response.json() == {"detail": "Prefecture search is unavailable."}
