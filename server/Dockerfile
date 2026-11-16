FROM python:3.14-slim-trixie AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgdal36 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /usr/local/bin/uv

RUN uv run --no-project --with duckdb==2.0.0 python -c "import duckdb; duckdb.install_extension('spatial')"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS worker
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates osm2pgsql \
    && rm -rf /var/lib/apt/lists/*

FROM base AS server
