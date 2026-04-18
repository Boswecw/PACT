# Runtime Serialization Boundary ADR
**Date:** 2026-04-17
**Time:** 20:30 UTC

## Decision
PACT keeps model-bound rendering inside the runtime serialization boundary and does not let downstream consumers redefine packet truth.

## Why
The packet remains canonical truth.
The serializer produces a governed artifact form only after packet construction and validation complete.

## Consequences
- packet schemas remain the source of truth
- serializer logic is explicit and bounded
- fallback and fail-closed behavior stay inside runtime control
- downstream consumers may inspect artifacts without owning packet semantics
