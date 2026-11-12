CREATE FUNCTION public.pipe_mvt(z integer, x integer, y integer, query_params json)
RETURNS bytea
LANGUAGE sql
STABLE
AS $$
    WITH request AS (
        SELECT
            CASE
                WHEN pg_input_is_valid(query_params->>'pipeset_id', 'uuid')
                THEN (query_params->>'pipeset_id')::uuid
            END AS pipeset_id,
            ST_TileEnvelope(z, x, y) AS bounds,
            ST_Transform(ST_TileEnvelope(z, x, y, margin => 64.0 / 4096), 4326) AS buffered_bounds
    ),
    tile AS (
        SELECT
            pipe.id,
            ST_AsMVTGeom(ST_Transform(pipe.geometry, 3857), request.bounds, 4096, 64) AS geom
        FROM public.pipesets_pipe AS pipe
        CROSS JOIN request
        WHERE pipe.pipeset_id = request.pipeset_id
          AND pipe.geometry && request.buffered_bounds
    )
    SELECT ST_AsMVT(tile, 'pipes', 4096, 'geom', 'id')
    FROM tile
    WHERE geom IS NOT NULL;
$$;
