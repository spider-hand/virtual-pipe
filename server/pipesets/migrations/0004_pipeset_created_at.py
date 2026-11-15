from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("pipesets", "0003_pipe_generation")]

    operations = [
        migrations.AddField(
            model_name="pipeset",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="pipeset",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
