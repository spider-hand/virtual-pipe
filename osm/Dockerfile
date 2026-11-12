FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl osm2pgsql postgresql-client util-linux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /osm
COPY region.sh download.sh import.sh roads.lua ./
