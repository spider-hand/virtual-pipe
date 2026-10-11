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
