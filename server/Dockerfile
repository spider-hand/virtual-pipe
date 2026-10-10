FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgdal36 libgeos-c1t64 \
    && rm -rf /var/lib/apt/lists/*
