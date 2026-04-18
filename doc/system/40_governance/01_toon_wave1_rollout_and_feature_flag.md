# TOON Wave 1 Rollout and Feature Flag ADR
**Date:** 2026-04-17
**Time:** 20:30 UTC

## Decision
TOON wave 1 ships behind `PACT_ENABLE_TOON_WAVE1`, default false.

## Why
Rollout must not outrun control.
Immediate disablement is required if determinism, receipt integrity, or renderer safety regresses.

## Consequences
- stage 1 supports internal implementation and proof only
- stage 2 allows shadow-mode inspection without production dependence
- stage 3 requires green proof gates before downstream reliance
- observability is required so the operator can measure requests, actual use, and fallback reasons
