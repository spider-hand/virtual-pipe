local roads = osm2pgsql.define_way_table('osm_roads', {
    { column = 'highway', type = 'text', not_null = true },
    { column = 'geometry', type = 'linestring', projection = 4326, not_null = true },
})

-- This project is inspired by water supply pipe networks.
-- Use ordinary roads as approximate pipe routes, excluding motorways, paths, and tracks.
local highways = {
    trunk = true, trunk_link = true,
    primary = true, primary_link = true,
    secondary = true, secondary_link = true,
    tertiary = true, tertiary_link = true,
    unclassified = true, residential = true,
    living_street = true, service = true,
}

function osm2pgsql.process_way(object)
    -- Also exclude road areas, motorroad-only routes, parking aisles, and driveways.
    if highways[object.tags.highway]
        and object.tags.area ~= 'yes'
        and object.tags.motorroad ~= 'yes'
        and not (object.tags.highway == 'service'
            and (object.tags.service == 'parking_aisle' or object.tags.service == 'driveway')) then
        roads:insert({
            highway = object.tags.highway,
            geometry = object:as_linestring(),
        })
    end
end
