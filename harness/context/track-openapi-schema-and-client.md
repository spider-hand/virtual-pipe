# Track the OpenAPI schema and generated client

**Status** Accepted

## Context

The Vue client needs types and a callable client that follow the Django REST API. Client generation requires Docker, and developers need to review changes to the API contract alongside the endpoint changes.

## Decision

Generate the OpenAPI schema from Django using drf-spectacular. Generate the TypeScript client from that schema using a pinned OpenAPI Generator image. Track both outputs in Git and regenerate them in that order whenever the API changes.

## Consequences

A clean checkout can build and test the Vue client immediately after installing dependencies. API changes include generated diffs, and developers changing the contract need Docker to regenerate the client.
