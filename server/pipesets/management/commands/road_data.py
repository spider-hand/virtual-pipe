import os
from subprocess import CalledProcessError

from django.core.management.base import BaseCommand, CommandError

from pipesets.road_data import download_roads, import_roads

OPERATIONS = {"download": download_roads, "import": import_roads}


class Command(BaseCommand):
    help = "Download or import the Geofabrik region specified by REGION."

    def add_arguments(self, parser):
        parser.add_argument("operation", choices=OPERATIONS)

    def handle(self, *args, **options):
        region = os.environ.get("REGION", "")
        operation = options["operation"]

        try:
            OPERATIONS[operation](region)
        except (ValueError, OSError, CalledProcessError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(f"Completed road data {operation} for {region}.")
        )
