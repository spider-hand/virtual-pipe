# Store attribute definitions as an ordered JSON array

**Status** Accepted

## Context

The editor saves an attribute set as one unit. The pipe generator will read the complete ordered definition. Attribute types have different settings.

## Decision

Store the ordered list in the attribute set's JSON field, with a Django REST Framework serializer for each attribute type. A related attribute table would allow direct queries and database-level name uniqueness. It would also require storing positions and coordinating writes across multiple rows when saving a set.

## Consequences

Creating a set writes one row and preserves attribute order and decimal precision. The API enforces the definition rules and name uniqueness within a set. Any future import path must use the same validation. Revisit relational storage if individual attributes need to be queried, edited, or referenced across sets.
