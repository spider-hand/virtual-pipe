FROM python:3.14-slim-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgdal36 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1
WORKDIR /app
