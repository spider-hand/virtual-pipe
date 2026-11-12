# Use shared PostgreSQL with PostGIS

**Status** Accepted

## Context

Django needs application storage, and imported OSM roads need spatial indexes and spatial queries. Local development supports running Django in Compose or directly on the host.

## Decision

Use one PostgreSQL database with PostGIS for both. Store imported roads in the `osm` schema. Django uses PostgreSQL from both Compose and the host.

## Consequences

A single service handles migrations and spatial queries. Host development and database-backed tests require a running PostgreSQL instance.
