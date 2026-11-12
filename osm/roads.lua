local highway_classes = {
    motorway = true,
    motorway_link = true,
    trunk = true,
    trunk_link = true,
    primary = true,
    primary_link = true,
    secondary = true,
    secondary_link = true,
    tertiary = true,
    tertiary_link = true,
    unclassified = true,
    residential = true,
    living_street = true,
    service = true,
}

local roads = osm2pgsql.define_table({
    name = 'roads',
    schema = 'osm_import',
    ids = { type = 'way', id_column = 'osm_id' },
    columns = {
        { column = 'highway', type = 'text', not_null = true },
        { column = 'name', type = 'text' },
        { column = 'geom', type = 'linestring', projection = 4326, not_null = true },
    },
    indexes = { { column = 'geom', method = 'gist' } },
})

function osm2pgsql.process_way(object)
    local highway = object.tags.highway
    if not highway_classes[highway] or object.tags.area == 'yes' then
        return
    end

    roads:insert({
        highway = highway,
        name = object.tags.name,
        geom = object:as_linestring(),
    })
end
