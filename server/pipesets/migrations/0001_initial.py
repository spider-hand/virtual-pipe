import uuid
from pathlib import Path

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

# Keep this initial definition fixed. Put updates and their reverse SQL in a later migration.
pipe_mvt_sql = Path(__file__).resolve().parents[1] / "functions" / "pipe_mvt.sql"


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS postgis;", migrations.RunSQL.noop
        ),
        migrations.CreateModel(
            name="PipeSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Pipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.LineStringField(srid=4326),
                ),
                (
                    "pipeset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="pipesets.pipeset",
                    ),
                ),
            ],
        ),
        migrations.RunSQL(
            sql=pipe_mvt_sql.read_text(encoding="utf-8"),
            reverse_sql="DROP FUNCTION public.pipe_mvt(integer, integer, integer, json);",
        ),
    ]
