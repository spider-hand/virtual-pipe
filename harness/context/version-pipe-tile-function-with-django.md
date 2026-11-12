# Version the pipe tile function with Django migrations

**Status** Accepted

## Context

The pipe tile function depends on the pipe tables. An update must work on existing databases, and rolling it back must restore the prior definition.

## Decision

Install the function in the initial Django migration. Put both the forward SQL and `reverse_sql` for a later body change directly in one new `RunSQL` migration, using `CREATE OR REPLACE FUNCTION` in both directions. Keep the SQL used by the initial migration fixed.

## Consequences

Django records function updates and can roll them back while preserving the pipe tables and data. Each update migration carries the SQL needed to restore the previous definition.
