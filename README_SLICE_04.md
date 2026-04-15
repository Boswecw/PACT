# PACT Slice 04 — Retrieval + Budget Bundle

## Date
2026-04-15

## Purpose
This zip provides the Slice 04 overlay.

Slice 04 adds:
- retrieval intake handling
- retrieval-mode degradation (`hybrid` -> `lexical_only` fallback)
- grounding-material selection into compile input
- rerank/pruning degradation handling
- class-budget enforcement
- one-shot budget reduction retry
- cache-degraded receipt state
- `scripts/verify_slice_04.py`
- `harness/regression/slice_04_cases.jsonl`

## Apply
Unzip this bundle into the root of:

```bash
~/Forge/ecosystem/pact
```

Then merge the extracted folder into repo root the same way as Slice 03.

## Verify
Run:

```bash
python3 scripts/verify_slice_04.py
```
