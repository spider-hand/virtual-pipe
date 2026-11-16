import uuid
from pathlib import Path

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

# Keep this SQL fixed so the initial migration remains reproducible.
pipe_mvt_sql = Path(__file__).resolve().parents[1] / "functions" / "pipe_mvt.sql"


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RoadDataSetup",
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
                ("region", models.CharField(max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("downloading", "Downloading"),
                            ("importing", "Importing"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                        ],
                        default="queued",
                        max_length=11,
                    ),
                ),
                (
                    "failure",
                    models.CharField(
                        choices=[
                            ("queue", "Queue"),
                            ("download", "Download"),
                            ("import", "Import"),
                        ],
                        max_length=8,
                        null=True,
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        models.Value(1),
                        condition=models.Q(
                            ("status__in", ["queued", "downloading", "importing"])
                        ),
                        name="only_one_active_road_data_setup",
                    )
                ],
            },
        ),
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS postgis;", migrations.RunSQL.noop
        ),
        migrations.CreateModel(
            name="AttributeSet",
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
                ("attributes", models.JSONField()),
            ],
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
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("district_id", models.CharField(blank=True, max_length=5)),
                ("prefecture_id", models.CharField(blank=True, max_length=2)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                        ],
                        default="succeeded",
                        max_length=9,
                    ),
                ),
                ("failure_reason", models.TextField(blank=True)),
                (
                    "attribute_set",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pipesets.attributeset",
                    ),
                ),
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
                ("attributes", models.JSONField(default=dict)),
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
