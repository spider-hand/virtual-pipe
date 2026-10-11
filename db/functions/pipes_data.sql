CREATE OR REPLACE FUNCTION pipes_data(selected_pipeset_id bigint)
RETURNS TABLE(id bigint, pipeset_id bigint, geometry geometry)
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT pipe.id, pipe.pipeset_id, pipe.geometry
    FROM pipesets_pipe AS pipe
    WHERE pipe.pipeset_id = selected_pipeset_id;
$$;
