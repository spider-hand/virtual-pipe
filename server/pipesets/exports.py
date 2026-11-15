import csv
from contextlib import closing
from itertools import batched
from pathlib import Path
from tempfile import TemporaryDirectory
from unicodedata import category

import duckdb
from django.contrib.gis.db.models.functions import AsWKT
from django.http import FileResponse

from pipesets.models import Pipe

GEOMETRY_COLUMN = "geometry"
EXPORT_CONTENT_TYPES = {
    "csv": "text/csv",
    "parquet": "application/vnd.apache.parquet",
}
BATCH_SIZE = 1000


class PipeSetExportResponse(FileResponse):
    def __init__(self, pipeset, definitions, file_format):
        self.directory = TemporaryDirectory(prefix="pipeset-export-")
        path = Path(self.directory.name) / f"export.{file_format}"
        name = "".join(
            "_" if char in "/\\" or category(char) == "Cc" else char
            for char in pipeset.name
        )

        try:
            columns = [definition["name"] for definition in definitions]
            with closing(pipe_rows(pipeset, columns)) as rows:
                headers = [*columns, GEOMETRY_COLUMN]
                if file_format == "csv":
                    with path.open("w", encoding="utf-8", newline="") as output:
                        writer = csv.writer(output)
                        writer.writerow(headers)
                        writer.writerows(rows)
                else:
                    write_parquet(path, headers, definitions, rows)

            file = path.open("rb")
            try:
                super().__init__(
                    file,
                    as_attachment=True,
                    filename=f"{name}.{file_format}",
                    content_type=EXPORT_CONTENT_TYPES[file_format],
                )
            except BaseException:
                file.close()
                raise
        except BaseException:
            self.directory.cleanup()
            raise

    def close(self):
        try:
            super().close()
        finally:
            self.directory.cleanup()


def pipe_rows(pipeset, columns):
    pipes = (
        Pipe.objects.filter(pipeset=pipeset)
        .order_by("pk")
        .annotate(wkt=AsWKT("geometry"))
        .values_list("attributes", "wkt")
    )

    for attributes, wkt in pipes.iterator(chunk_size=BATCH_SIZE):
        yield (*(attributes.get(column) for column in columns), wkt)


def parquet_type(definition):
    match definition["type"]:
        case "boolean":
            return "BOOLEAN"
        case "date":
            return "DATE"
        case "integer":
            if -(2**63) <= int(definition["min"]) and int(definition["max"]) < 2**63:
                return "BIGINT"
        case "decimal":
            lower, upper = (
                bound.lstrip("-").split(".")
                for bound in (definition["min"], definition["max"])
            )
            precision = max(len(lower[0].lstrip("0")), len(upper[0].lstrip("0"))) + len(
                lower[1]
            )
            if precision <= 38:
                return f"DECIMAL({precision}, {len(lower[1])})"

    return "VARCHAR"


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def write_parquet(path, columns, definitions, rows):
    types = [*(parquet_type(definition) for definition in definitions), "VARCHAR"]
    # Use positional staging names so user-defined columns cannot collide with row ordering.
    staging_columns = [f"column_{index}" for index in range(len(columns))]
    declarations = ", ".join(
        f"{column} {column_type}"
        for column, column_type in zip(staging_columns, types, strict=True)
    )
    projection = ", ".join(
        f"{source} AS {quote_identifier(name)}"
        for source, name in zip(staging_columns, columns, strict=True)
    )
    values_query = ", ".join(
        f"CAST(unnest(?::VARCHAR[]) AS {column_type})" for column_type in types
    )

    database = path.with_suffix(".duckdb")
    with duckdb.connect(
        str(database), config={"memory_limit": "128MB", "threads": 1}
    ) as connection:
        connection.execute(f"CREATE TABLE pipes (row_number BIGINT, {declarations})")
        row_number = 0
        for batch in batched(rows, BATCH_SIZE):
            values = [
                [str(value) if value is not None else None for value in column]
                for column in zip(*batch, strict=True)
            ]
            row_numbers = list(range(row_number, row_number + len(batch)))
            connection.execute(
                f"INSERT INTO pipes SELECT unnest(?::BIGINT[]), {values_query}",
                [row_numbers, *values],
            )
            row_number += len(batch)

        connection.execute(
            f"COPY (SELECT {projection} FROM pipes ORDER BY row_number) TO ? (FORMAT PARQUET)",
            [str(path)],
        )

    database.unlink()
