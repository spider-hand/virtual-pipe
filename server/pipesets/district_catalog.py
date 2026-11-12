import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

DATA_DIR = Path(
    os.environ.get("DISTRICT_DATA_DIR", Path(__file__).resolve().parents[2] / "data")
)
SOURCE = DATA_DIR / "N03-20260101.shp"
CATALOG = DATA_DIR / "districts-2026.duckdb"

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
                CREATE TABLE districts AS
                WITH boundaries AS (
                    SELECT
                        trim(N03_007) AS code,
                        trim(N03_001) AS prefecture,
                        nullif(trim(N03_003), '') AS county,
                        trim(N03_004) AS municipality,
                        nullif(trim(N03_005), '') AS ward,
                        ST_Transform(geom, 'EPSG:6668', 'EPSG:4326', always_xy := true) AS boundary
                    FROM ST_Read(?)
                    WHERE regexp_full_match(trim(N03_007), '[0-9]{5}')
                        AND trim(N03_004) <> ''
                        AND geom IS NOT NULL
                        AND NOT ST_IsEmpty(geom)
                )
                SELECT
                    code,
                    municipality,
                    ward,
                    concat_ws(' ', prefecture, county, municipality, ward) AS label,
                    [min(ST_XMin(boundary)), min(ST_YMin(boundary)),
                     max(ST_XMax(boundary)), max(ST_YMax(boundary))] AS bounds
                FROM boundaries
                GROUP BY code, prefecture, county, municipality, ward
                """,
                [str(SOURCE)],
            )
            if not connection.execute("SELECT count(*) FROM districts").fetchone()[0]:
                raise ValueError("The shapefile contains no searchable districts")

        catalog.replace(CATALOG)


def search_districts(query):
    if not CATALOG.is_file():
        return None

    with duckdb.connect(str(CATALOG), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT code, label, bounds
            FROM districts
            WHERE contains(replace(label, ' ', ''), $query)
            ORDER BY CASE
                WHEN municipality = $query OR ward = $query THEN 0
                WHEN starts_with(municipality, $query) OR starts_with(ward, $query)
                    OR starts_with(replace(label, ' ', ''), $query) THEN 1
                ELSE 2
            END, label, code
            LIMIT 10
            """,
            {"query": query},
        ).fetchall()

    return [
        {"code": code, "label": label, "bounds": bounds} for code, label, bounds in rows
    ]


if __name__ == "__main__":
    try:
        prepare_catalog()
    except OSError, ValueError, duckdb.Error:
        logger.exception(
            "District search unavailable. Check the shapefile and sidecars in %s.",
            DATA_DIR,
        )
