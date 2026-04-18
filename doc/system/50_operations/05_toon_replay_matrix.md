# TOON Wave 1 Replay Matrix
**Date:** 2026-04-17
**Time:** 22:00 UTC

## Purpose
Keep a fixture-driven replay matrix for the admitted wave-1 TOON cases.

## Inputs
- `tests/fixtures/toon_wave1_replay_cases.json`

## Command
```bash
python3 scripts/verify_toon_replay_matrix.py
```

## Output
- `docs/evidence/toon_replay_matrix_report.json`

## Fail posture
If any fixture case changes behavior outside the admitted expectations, the replay matrix proof fails.
