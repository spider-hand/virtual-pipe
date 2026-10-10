from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("pipesets", "0002_pipe")]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE osm_roads (
                way_id bigint NOT NULL,
                highway text NOT NULL,
                geometry geometry(LineString, 4326) NOT NULL
            );
            CREATE INDEX osm_roads_geometry_idx ON osm_roads USING gist (geometry);
            """,
            "DROP TABLE osm_roads;",
        ),
        migrations.RunSQL(
            """
            CREATE FUNCTION pipes_tile(z integer, x integer, y integer, query json)
            RETURNS bytea LANGUAGE sql STABLE PARALLEL SAFE AS $$
                SELECT ST_AsMVT(tile, 'pipes', 4096, 'geometry', 'id')
                FROM (
                    SELECT id, pipeset_id,
                        ST_AsMVTGeom(
                            ST_Transform(geometry, 3857),
                            ST_TileEnvelope(z, x, y), 4096, 64, true
                        ) AS geometry
                    FROM pipesets_pipe
                    WHERE pipeset_id = CASE
                        WHEN query->>'pipeset_id' ~ '^[0-9]{1,18}$'
                        THEN (query->>'pipeset_id')::bigint
                    END
                    AND geometry && ST_Transform(
                        ST_TileEnvelope(z, x, y, margin => 64.0 / 4096), 4326
                    )
                ) AS tile
                WHERE geometry IS NOT NULL;
            $$;
            """,
            "DROP FUNCTION pipes_tile(integer, integer, integer, json);",
        ),
    ]
