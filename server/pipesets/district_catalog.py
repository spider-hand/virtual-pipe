import logging
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

DATA_DIR = Path(
    os.environ.get("DISTRICT_DATA_DIR", Path(__file__).resolve().parents[2] / "data")
)
SOURCE = DATA_DIR / "N03-20260101.shp"
CATALOG = DATA_DIR / "districts-2026-v5.duckdb"

logger = logging.getLogger(__name__)


def prepare_catalog():
    if CATALOG.is_file():
        return

    with TemporaryDirectory(dir=DATA_DIR) as temporary:
        catalog = Path(temporary) / CATALOG.name

        with duckdb.connect(str(catalog)) as connection:
            connection.execute("LOAD spatial")
            connection.execute(
                """
                CREATE TEMP TABLE municipal_names AS
                SELECT code, pref_en, city_en
                FROM read_csv(?, header = true, all_varchar = true)
                """,
                [str(DATA_DIR / "municipal_names.csv")],
            )
            connection.execute(
                """
                CREATE TEMP TABLE boundaries AS
                SELECT
                    trim(N03_007) AS code,
                    trim(N03_001) AS prefecture,
                    nullif(trim(N03_003), '') AS county,
                    trim(N03_004) AS municipality,
                    nullif(trim(N03_005), '') AS ward,
                    ST_Transform(geom, 'EPSG:6668', 'EPSG:4326', always_xy := true) AS boundary
                FROM ST_Read(?)
                WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom)
                """,
                [str(SOURCE)],
            )
            connection.execute(
                """
                CREATE TABLE districts AS
                WITH districts AS (
                    SELECT
                        code,
                        first(municipality ORDER BY label) AS municipality,
                        first(ward ORDER BY label) AS ward,
                        min(label) AS label,
                        ST_CollectionExtract(ST_Union_Agg(ST_MakeValid(boundary)), 3)
                            AS boundary
                    FROM (
                        SELECT *, concat_ws(' ', prefecture, county, municipality, ward)
                            AS label
                        FROM boundaries
                        WHERE regexp_full_match(code, '[0-9]{5}') AND municipality <> ''
                    )
                    GROUP BY code
                )
                SELECT
                    districts.code,
                    municipality,
                    ward,
                    label,
                    names.city_en,
                    CASE WHEN names.city_en IS NOT NULL
                        THEN concat_ws(' ', names.pref_en, names.city_en)
                    END AS label_en,
                    [ST_XMin(boundary), ST_YMin(boundary),
                     ST_XMax(boundary), ST_YMax(boundary)] AS bounds,
                    ST_AsWKB(boundary) AS boundary_wkb
                FROM districts
                LEFT JOIN municipal_names AS names ON districts.code = names.code
                WHERE ST_GeometryType(boundary) IN ('POLYGON', 'MULTIPOLYGON')
                    AND NOT ST_IsEmpty(boundary)
                """,
            )
            if not connection.execute("SELECT count(*) FROM districts").fetchone()[0]:
                raise ValueError("The shapefile contains no searchable districts")

            connection.execute(
                """
                CREATE TABLE prefectures AS
                WITH prefectures AS (
                    SELECT
                        min(left(code, 2)) FILTER (WHERE regexp_full_match(code, '[0-9]{5}'))
                            AS code,
                        prefecture AS label,
                        ST_CollectionExtract(ST_Union_Agg(ST_MakeValid(boundary)), 3)
                            AS boundary
                    FROM boundaries
                    WHERE prefecture <> ''
                    GROUP BY prefecture
                )
                SELECT
                    prefectures.code,
                    label,
                    names.pref_en AS label_en,
                    [ST_XMin(boundary), ST_YMin(boundary),
                     ST_XMax(boundary), ST_YMax(boundary)] AS bounds,
                    ST_AsWKB(boundary) AS boundary_wkb
                FROM prefectures
                LEFT JOIN municipal_names AS names ON names.code = prefectures.code || '000'
                WHERE prefectures.code IS NOT NULL
                    AND ST_GeometryType(boundary) IN ('POLYGON', 'MULTIPOLYGON')
                    AND NOT ST_IsEmpty(boundary)
                """
            )
            if not connection.execute("SELECT count(*) FROM prefectures").fetchone()[0]:
                raise ValueError("The shapefile contains no searchable prefectures")

        catalog.replace(CATALOG)


def get_district(code):
    with duckdb.connect(str(CATALOG), read_only=True) as connection:
        return connection.execute(
            "SELECT label, boundary_wkb FROM districts WHERE code = ?", [code]
        ).fetchone()


def get_prefecture(code):
    with duckdb.connect(str(CATALOG), read_only=True) as connection:
        return connection.execute(
            "SELECT label, boundary_wkb FROM prefectures WHERE code = ?", [code]
        ).fetchone()


def search_districts(query):
    if not CATALOG.is_file():
        return None

    query_en = re.sub(r"[\s,\-]", "", query.lower())

    with duckdb.connect(str(CATALOG), read_only=True) as connection:
        rows = connection.execute(
            """
            WITH searchable AS (
                SELECT *,
                    regexp_replace(lower(label_en), '[[:space:],-]', '', 'g') AS search_en,
                    regexp_replace(lower(split_part(city_en, ',', 1)), '[[:space:]-]', '', 'g')
                        AS municipality_en,
                    regexp_replace(lower(split_part(city_en, ',', 2)), '[[:space:]-]', '', 'g')
                        AS ward_en
                FROM districts
            )
            SELECT code, label, label_en, bounds
            FROM searchable
            WHERE contains(replace(label, ' ', ''), $query)
                OR ($query_en <> '' AND contains(search_en, $query_en))
            ORDER BY CASE
                WHEN municipality = $query OR ward = $query
                    OR municipality_en = $query_en OR ward_en = $query_en THEN 0
                WHEN starts_with(municipality, $query) OR starts_with(ward, $query)
                    OR starts_with(replace(label, ' ', ''), $query)
                    OR ($query_en <> '' AND (
                        starts_with(municipality_en, $query_en) OR starts_with(ward_en, $query_en)
                        OR starts_with(search_en, $query_en)
                    )) THEN 1
                ELSE 2
            END, label, code
            LIMIT 10
            """,
            {"query": query, "query_en": query_en},
        ).fetchall()

    return [
        {"code": code, "label": label, "label_en": label_en, "bounds": bounds}
        for code, label, label_en, bounds in rows
    ]


def list_prefectures():
    if not CATALOG.is_file():
        return None

    with duckdb.connect(str(CATALOG), read_only=True) as connection:
        rows = connection.execute(
            "SELECT code, label, label_en, bounds FROM prefectures ORDER BY code"
        ).fetchall()

    return [
        {"code": code, "label": label, "label_en": label_en, "bounds": bounds}
        for code, label, label_en, bounds in rows
    ]


if __name__ == "__main__":
    try:
        prepare_catalog()
    except OSError, ValueError, duckdb.Error:
        logger.exception(
            "District and prefecture search unavailable. "
            "Check the shapefile, sidecars, and municipal names CSV in %s.",
            DATA_DIR,
        )
