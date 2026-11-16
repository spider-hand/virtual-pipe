import fcntl
import hashlib
import os
import subprocess
from pathlib import Path
from stat import S_ISREG
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from django.db import connection, transaction
from psycopg import sql

REGIONS = (
    "japan",
    "chubu",
    "chugoku",
    "hokkaido",
    "kansai",
    "kanto",
    "kyushu",
    "shikoku",
    "tohoku",
)
DOWNLOADS = Path("/downloads")
GEOFABRIK = "https://download.geofabrik.de"


def extract_path(region):
    if region not in REGIONS:
        raise ValueError(f"Set REGION to one of: {' '.join(REGIONS)}")

    return DOWNLOADS / f"{region}.osm.pbf"


def has_cached_extract(region):
    try:
        cached = extract_path(region).stat()
    except FileNotFoundError:
        return False

    return S_ISREG(cached.st_mode) and cached.st_size > 0


def download_roads(region):
    path = extract_path(region)
    extract = "asia/japan" if region == "japan" else f"asia/japan/{region}"
    url = f"{GEOFABRIK}/{extract}-latest.osm.pbf"
    digest = hashlib.md5(usedforsecurity=False)

    with NamedTemporaryFile(
        dir=path.parent, prefix=f"{path.name}.", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with urlopen(url, timeout=60) as response:
                checksum_url = f"{response.url}.md5"
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    temporary.write(chunk)

            with urlopen(checksum_url, timeout=60) as response:
                checksum = response.read(1024).split(maxsplit=1)[:1]

            if checksum != [digest.hexdigest().encode("ascii")]:
                raise ValueError(f"Checksum verification failed for {region}.")

            temporary.close()
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)


def import_roads(region):
    path = extract_path(region)
    if not has_cached_extract(region):
        raise ValueError(
            f"No cached extract for {region}. Run make osm:download REGION={region} first."
        )

    with (path.parent / "import.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS osm_import CASCADE")
            cursor.execute("CREATE SCHEMA osm_import")

        db = connection.settings_dict
        subprocess.run(
            [
                "osm2pgsql",
                "--create",
                "--slim",
                "--drop",
                "--cache",
                "512",
                "--schema",
                "osm_import",
                "--output",
                "flex",
                "--style",
                "/osm/roads.lua",
                str(path),
            ],
            env={
                **os.environ,
                "PGHOST": db["HOST"],
                "PGPORT": db["PORT"],
                "PGDATABASE": db["NAME"],
                "PGUSER": db["USER"],
                "PGPASSWORD": db["PASSWORD"],
            },
            check=True,
            pass_fds=(lock.fileno(),),
        )

        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT FROM osm_import.roads)")
            if not cursor.fetchone()[0]:
                raise ValueError("The extract contains no eligible roads.")

            cursor.execute("ALTER TABLE osm_import.roads ADD PRIMARY KEY (osm_id)")
            cursor.execute("DROP TABLE IF EXISTS osm.roads")
            cursor.execute("ALTER TABLE osm_import.roads SET SCHEMA osm")
            cursor.execute(
                sql.SQL("COMMENT ON TABLE osm.roads IS {}")
                .format(sql.Literal(region))
                .as_string()
            )
            cursor.execute("DROP SCHEMA osm_import CASCADE")


def get_coverage():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT roads IS NOT NULL, obj_description(roads, 'pg_class') "
            "FROM (SELECT to_regclass('osm.roads') AS roads) AS coverage"
        )
        has_roads, region = cursor.fetchone()

    return {
        "has_roads": has_roads,
        "active_region": region if region in REGIONS else None,
    }
