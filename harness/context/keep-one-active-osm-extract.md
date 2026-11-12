# Keep one active OSM extract

**Status** Accepted

## Context

Geofabrik supplies a nationwide Japan extract and smaller regional extracts. A regional extract is sufficient for many demo workflows, and regional extracts can contain overlapping ways near their boundaries.

## Decision

Keep one active extract in `osm.roads`. Import into staging and publish in a transaction only after the staged roads pass validation.

## Consequences

Changing regions is a full replacement and avoids merging overlapping ways. Readers can keep using the previous dataset while the import builds, at the cost of disk space for staging.
