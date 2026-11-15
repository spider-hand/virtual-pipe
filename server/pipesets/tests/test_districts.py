import json

import duckdb
import pytest

from pipesets import district_catalog as catalog_builder


@pytest.fixture
def district_catalog(tmp_path, monkeypatch):
    catalog = tmp_path / "districts.duckdb"
    monkeypatch.setattr("pipesets.district_catalog.CATALOG", catalog)

    with duckdb.connect(str(catalog)) as connection:
        connection.execute(
            """
            CREATE TABLE districts AS
            SELECT code, municipality, ward, label, bounds
            FROM (VALUES
                ('13206', '府中市', NULL, '東京都 府中市', [139.4, 35.6, 139.6, 35.7]),
                ('34208', '府中市', NULL, '広島県 府中市', [133.1, 34.5, 133.4, 34.8]),
                ('14104', '横浜市', '中区', '神奈川県 横浜市 中区', [139.5, 35.4, 139.7, 35.5]),
                ('01234', '中区町', NULL, '北海道 中区町', [141.0, 43.0, 142.0, 44.0])
            ) AS entries(code, municipality, ward, label, bounds)
            """
        )

    return catalog


@pytest.mark.parametrize(
    ("query", "codes"),
    [
        ("府中市", ["34208", "13206"]),
        ("中区", ["14104", "01234"]),
        ("横浜", ["14104"]),
        ("神奈川県 横浜市", ["14104"]),
        ("浜市", ["14104"]),
    ],
)
def test_search_returns_ranked_districts_with_bounds(
    client, district_catalog, query, codes
):
    response = client.get("/api/districts/", {"q": query})

    assert response.status_code == 200
    results = response.json()
    assert [district["code"] for district in results] == codes
    if results[0]["code"] == "14104":
        assert results[0] == {
            "code": "14104",
            "label": "神奈川県 横浜市 中区",
            "bounds": [139.5, 35.4, 139.7, 35.5],
        }


@pytest.mark.parametrize("query", ["", "   ", "該当なし", "%"])
def test_search_returns_empty_results_for_blank_or_unmatched_text(
    client, district_catalog, query
):
    response = client.get("/api/districts/", {"q": query})

    assert response.status_code == 200
    assert response.json() == []


def test_search_limits_suggestions_to_ten(client, district_catalog):
    with duckdb.connect(str(district_catalog)) as connection:
        connection.execute(
            """
            INSERT INTO districts
            SELECT lpad(i::VARCHAR, 5, '0'), '試験町', NULL, '試験県 試験町', [130, 31, 131, 32]
            FROM range(12) AS rows(i)
            """
        )

    response = client.get("/api/districts/", {"q": "試験町"})

    assert response.status_code == 200
    assert [district["code"] for district in response.json()] == [
        f"{i:05d}" for i in range(10)
    ]


def test_search_reports_unavailable_when_catalog_is_missing(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "pipesets.district_catalog.CATALOG", tmp_path / "missing.duckdb"
    )

    assert client.get("/api/districts/", {"q": "府中市"}).status_code == 503
    assert client.get("/api/health/").status_code == 200


def test_catalog_dissolves_districts_and_preserves_islands_and_prefecture_borders(
    tmp_path, monkeypatch
):
    source = tmp_path / "boundaries.geojson"
    catalog = tmp_path / "areas.duckdb"
    monkeypatch.setattr(catalog_builder, "DATA_DIR", tmp_path)
    monkeypatch.setattr(catalog_builder, "SOURCE", source)
    monkeypatch.setattr(catalog_builder, "CATALOG", catalog)

    features = []
    for prefecture, municipality, code, west in [
        ("北海道", "試験市", "01001", 140),
        ("北海道", "試験町", "01002", 141),
        ("北海道", "", "", 144),
        ("青森県", "試験村", "02001", 142),
    ]:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "N03_001": prefecture,
                    "N03_003": "",
                    "N03_004": municipality,
                    "N03_005": "",
                    "N03_007": code,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [west, 40],
                            [west + 1, 40],
                            [west + 1, 41],
                            [west, 41],
                            [west, 40],
                        ]
                    ],
                },
            }
        )
    source.write_text(json.dumps({"type": "FeatureCollection", "features": features}))

    catalog_builder.prepare_catalog()

    with duckdb.connect(str(catalog), read_only=True) as connection:
        connection.execute("LOAD spatial")
        assert connection.execute(
            "SELECT code FROM districts ORDER BY code"
        ).fetchall() == [
            ("01001",),
            ("01002",),
            ("02001",),
        ]
        rows = connection.execute(
            """
            SELECT code, label, bounds, ST_NumGeometries(boundary), ST_Area(boundary),
                ST_IsValid(boundary)
            FROM (
                SELECT *, ST_GeomFromWKB(boundary_wkb) AS boundary
                FROM prefectures
            )
            ORDER BY code
            """
        ).fetchall()

    assert rows == [
        ("01", "北海道", [140, 40, 145, 41], 2, 3, True),
        ("02", "青森県", [142, 40, 143, 41], 1, 1, True),
    ]
