FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends osm2pgsql osmium-tool curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data
