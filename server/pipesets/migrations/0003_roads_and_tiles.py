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
    ]
