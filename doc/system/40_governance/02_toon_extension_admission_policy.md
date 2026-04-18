# TOON Extension Admission Policy
**Date:** 2026-04-17
**Time:** 21:10 UTC

## Decision
New TOON capability classes are not admitted by silent registry edits.

## Wave 1 allowed state
- capability class: `wave1_ranked_result_segment`
- admission stage: `wave1_internal`
- packet allow-list: `search_assist_packet` only
- field order: `rank`, `title`, `source_ref`, `summary`

## Required for any future extension
1. new schema or schema version if the row contract changes
2. updated loader validation
3. new verification script or expanded proof gate
4. new operator evidence example
5. explicit approval before repo gate accepts the change

## Fail posture
If the registry drifts from the admitted wave-1 state without the matching governance work, the extension governance proof must fail.
