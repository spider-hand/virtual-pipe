set -eu

. ./region.sh

if [ ! -s "$pbf" ]; then
    printf 'No cached extract for %s. Run make osm:download REGION=%s first.\n' "$REGION" "$REGION" >&2
    exit 1
fi

export PGHOST="$POSTGRES_HOST" PGPORT="$POSTGRES_PORT" PGDATABASE="$POSTGRES_DB"
export PGUSER="$POSTGRES_USER" PGPASSWORD="$POSTGRES_PASSWORD"

exec 9>/downloads/import.lock
flock 9

psql -X -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA IF EXISTS osm_import CASCADE;
CREATE SCHEMA osm_import;
SQL

osm2pgsql --create --slim --drop --cache 512 --schema osm_import \
    --output flex --style roads.lua "$pbf"

psql -X -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM osm_import.roads) THEN
        RAISE EXCEPTION 'The extract contains no eligible roads';
    END IF;
END
$$;

ALTER TABLE osm_import.roads ADD PRIMARY KEY (osm_id);
DROP TABLE IF EXISTS osm.roads;
ALTER TABLE osm_import.roads SET SCHEMA osm;
DROP SCHEMA osm_import CASCADE;

COMMIT;
SQL

printf 'Imported %s into osm.roads.\n' "$REGION"
