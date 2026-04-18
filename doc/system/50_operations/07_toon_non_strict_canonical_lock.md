# TOON Wave 1 Non-Strict Canonical Lock
**Date:** 2026-04-17
**Time:** 22:35 UTC

## Purpose
Add canonical semantic locking for the non-strict replay cases whose raw artifact hashes are not yet stable.

## Inputs
- `tests/fixtures/toon_wave1_replay_cases.json`
- `tests/fixtures/toon_wave1_non_strict_canonical_targets.json`

## Command
```bash
python3 scripts/verify_toon_non_strict_canonical.py
```

## Output
- `docs/evidence/toon_non_strict_canonical_report.json`

## Fail posture
If fallback or fail-closed semantics drift on admitted fields, the canonical lock fails even when raw artifact hashes are allowed to vary.
