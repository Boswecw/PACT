# TOON Wave 1 Promotion Packet
**Date:** 2026-04-17
**Time:** 21:25 UTC

## Purpose
Freeze the wave-1 proof state into a single operator-reviewable packet.

## Command
```bash
python3 scripts/verify_toon_promotion_packet.py
```

## Output
- `docs/evidence/toon_wave1_promotion_packet.json`

## Contents
The packet records the current hash and byte size for the core wave-1 evidence files, governance documents, registry, and registry schema.

## Fail posture
If any required evidence file is missing, or if an upstream verifier fails, the promotion packet build fails.
