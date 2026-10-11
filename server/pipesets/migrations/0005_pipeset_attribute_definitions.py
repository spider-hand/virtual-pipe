from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("pipesets", "0004_remove_pipeset_count")]

    operations = [
        migrations.AddField(
            model_name="pipeset",
            name="attribute_definitions",
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.RunSQL(
            sql="""
DROP FUNCTION IF EXISTS pipes_mvt(integer, integer, integer, json);
DROP FUNCTION IF EXISTS pipes_data(bigint);
CREATE OR REPLACE FUNCTION pipes_data(selected_pipeset_id bigint)
RETURNS TABLE(id bigint, pipeset_id bigint, geometry geometry, attributes jsonb)
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT pipe.id, pipe.pipeset_id, pipe.geometry, pipe.attributes
    FROM pipesets_pipe AS pipe
    WHERE pipe.pipeset_id = selected_pipeset_id;
$$;
CREATE OR REPLACE FUNCTION pipes_mvt(z integer, x integer, y integer, query json)
RETURNS bytea LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT ST_AsMVT(tile, 'pipes', 4096, 'geometry', 'id')
    FROM (
        SELECT id, pipeset_id, attributes,
            ST_AsMVTGeom(
                ST_Transform(geometry, 3857),
                ST_TileEnvelope(z, x, y), 4096, 64, true
            ) AS geometry
        FROM pipes_data((query->>'pipeset_id')::bigint)
        WHERE geometry && ST_Transform(
            ST_TileEnvelope(z, x, y, margin => 64.0 / 4096), 4326
        )
    ) AS tile
    WHERE geometry IS NOT NULL;
$$;
""",
            reverse_sql="""
DROP FUNCTION IF EXISTS pipes_mvt(integer, integer, integer, json);
DROP FUNCTION IF EXISTS pipes_data(bigint);
CREATE OR REPLACE FUNCTION pipes_data(selected_pipeset_id bigint)
RETURNS TABLE(id bigint, pipeset_id bigint, geometry geometry)
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT pipe.id, pipe.pipeset_id, pipe.geometry
    FROM pipesets_pipe AS pipe
    WHERE pipe.pipeset_id = selected_pipeset_id;
$$;
CREATE OR REPLACE FUNCTION pipes_mvt(z integer, x integer, y integer, query json)
RETURNS bytea LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT ST_AsMVT(tile, 'pipes', 4096, 'geometry', 'id')
    FROM (
        SELECT id, pipeset_id,
            ST_AsMVTGeom(
                ST_Transform(geometry, 3857),
                ST_TileEnvelope(z, x, y), 4096, 64, true
            ) AS geometry
        FROM pipes_data((query->>'pipeset_id')::bigint)
        WHERE geometry && ST_Transform(
            ST_TileEnvelope(z, x, y, margin => 64.0 / 4096), 4326
        )
    ) AS tile
    WHERE geometry IS NOT NULL;
$$;
""",
        ),
    ]
