# PACT Slice 03 — Runtime Foundation Bundle

## Date
2026-04-15

## Purpose
This zip provides the next file set for Slice 03.

It is intentionally bounded to:
- intake normalization
- packet-base construction
- packet compilation for the three locked V1 packet classes
- schema validation against the existing `99-contracts/`
- safe-failure packet construction
- runtime receipt skeletons
- a deterministic Slice 03 verification script
- a small regression case set for this slice

It does **not** start:
- live retrieval
- reranking
- pruning engines
- TOON emission
- cache reuse logic
- model invocation

## Apply
Unzip this bundle into the root of the live repo:

```bash
~/Forge/ecosystem/pact
```

## Verify
Run:

```bash
python3 scripts/verify_slice_03.py
```

## Files included
- `runtime/engine.py`
- `runtime/intake/request_normalizer.py`
- `runtime/compiler/packet_base_builder.py`
- `runtime/compiler/packet_compiler.py`
- `runtime/compiler/safe_failure_builder.py`
- `runtime/validation/schema_validator.py`
- `runtime/receipts/runtime_receipt_builder.py`
- `src/shared/pact_utils.py`
- `harness/regression/slice_03_cases.jsonl`
- `scripts/verify_slice_03.py`
