# Serve pipe tiles through Martin

**Status** Accepted

## Context

The map needs vector tiles scoped to a pipe set. Django manages the pipe data in PostgreSQL, and PostGIS can encode the geometries as vector tiles.

## Decision

Publish the PostGIS tile function through Martin and route same-origin tile requests through Vite during local development. A Django tile endpoint would give Django control over each request. The local map can use Martin directly because it already knows which pipe set to render.

## Consequences

MapLibre can request tiles directly through the Vite proxy. Martin startup depends on Django migrations, and the tile function and the map must agree on the layer name and pipe set parameter.
