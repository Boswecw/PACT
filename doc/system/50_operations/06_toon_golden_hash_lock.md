# TOON Wave 1 Golden Hash Lock
**Date:** 2026-04-17
**Time:** 22:15 UTC

## Purpose
Freeze the admitted wave-1 replay outputs to exact artifact hashes.

## Inputs
- `tests/fixtures/toon_wave1_replay_cases.json`
- `tests/fixtures/toon_wave1_golden_hashes.json`

## Command
```bash
python3 scripts/verify_toon_golden_hashes.py
```

## Output
- `docs/evidence/toon_golden_hashes_report.json`

## Fail posture
If any admitted replay case changes artifact hash, the golden-hash proof fails.
