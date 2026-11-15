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
            CREATE TABLE prefectures (code VARCHAR, label VARCHAR, bounds DOUBLE[])
            """
        )
        connection.executemany(
            "INSERT INTO prefectures VALUES (?, ?, [130, 31, 131, 32])",
            [
                ("01", "北海道"),
                ("02", "北海"),
                ("03", "北海県"),
                ("04", "中北海県"),
                ("05", "テスト県"),
                *[(str(i), "試験県") for i in range(21, 9, -1)],
            ],
        )

    return catalog


@pytest.mark.parametrize(
    ("query", "codes"),
    [
        ("北海", ["02", "03", "01", "04"]),
        ("　北 海 道　", ["01"]),
        ("海道", ["01"]),
        ("　ﾃ ｽ ﾄ　", ["05"]),
    ],
)
def test_search_returns_ranked_prefectures(client, prefecture_catalog, query, codes):
    response = client.get("/api/prefectures/", {"q": query})

    assert response.status_code == 200
    assert [result["code"] for result in response.json()] == codes


def test_search_preserves_prefecture_codes_and_returns_bounds(
    client, prefecture_catalog
):
    response = client.get("/api/prefectures/", {"q": "北海道"})

    assert response.status_code == 200
    assert response.json() == [
        {"code": "01", "label": "北海道", "bounds": [130, 31, 131, 32]}
    ]


def test_search_limits_tied_prefectures_to_ten_by_code(client, prefecture_catalog):
    response = client.get("/api/prefectures/", {"q": "試験県"})

    assert response.status_code == 200
    assert [result["code"] for result in response.json()] == [
        str(i) for i in range(10, 20)
    ]


@pytest.mark.parametrize("params", [{}, {"q": "　 "}, {"q": "該当なし"}, {"q": "%"}])
def test_search_returns_empty_results_for_blank_or_unmatched_queries(
    client, prefecture_catalog, params
):
    response = client.get("/api/prefectures/", params)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("unavailable", ["missing", "unreadable"])
def test_search_reports_an_unavailable_catalog(
    client, tmp_path, monkeypatch, unavailable
):
    catalog = tmp_path / "areas.duckdb"
    monkeypatch.setattr(district_catalog, "CATALOG", catalog)
    if unavailable == "unreadable":
        catalog.write_text("not a DuckDB database")

    response = client.get("/api/prefectures/", {"q": "北海道"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Prefecture search is unavailable."}
