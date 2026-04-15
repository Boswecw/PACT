# PACT Slice 01 — Repo Foundation and Contract Bundle

## Slice boundary

This slice creates the **repo-start foundation** for PACT V1.

It is intentionally bounded to:
- the repo skeleton
- the initial contract bundle in `99-contracts/`
- starter corpus scaffolding
- harness scaffolding
- runtime/control/adapter/telemetry directory boundaries
- plan and protocol placement under `docs/`
- one deterministic verification script for this slice

It does **not** start runtime request-path implementation yet.

## Why this is Slice 01

The locked plan set says runtime coding should not begin until:
- contract artifacts exist
- repo boundaries are explicit
- the starter corpus is started
- verification posture is materially present

This slice gives you that foundation first.

## Apply

Create or enter the target PACT repo root, then unzip this slice into that root.

## Verify

Run:

```bash
python3 scripts/verify_slice_01.py
```

## Success criteria

Success for Slice 01 means:
- the repo skeleton exists
- all required contract files exist and parse
- fixtures exist for each locked schema
- corpus seed files exist and parse
- plan docs are placed under `docs/`
- the verification script exits successfully
# PACT Slice 02 — Contract Validation and Corpus Runner

## Slice boundary

This slice builds on Slice 01 and stays inside the pre-runtime readiness zone.

It adds:
- machine validation of every schema fixture using JSON Schema
- generated contract validation reporting
- corpus linting and class coverage checks
- a stricter Slice 02 verification script
- starter corpus expansion to satisfy the immediate early-floor posture:
  - 10 golden success cases
  - 5 combined degraded / safe-failure cases
  - explicit serialization mismatch corpus coverage

It does **not** start live runtime request-path implementation yet.

## Apply

From the existing PACT repo root created by Slice 01:

```bash
unzip -o slice_02_pact_contract_validation_and_corpus_runner.zip
python3 scripts/verify_slice_02.py
```
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
# PACT Slice 05 — Adapters + Replay/Live + Telemetry Bundle

## Date
2026-04-15

This overlay adds:
- retrieval provider contract surface
- cache provider contract surface
- replay vs live execution mode split
- in-memory live provider for proving
- telemetry/report emission to JSON artifacts
- `execute_slice_05`
- `scripts/verify_slice_05.py`
- `harness/regression/slice_05_cases.jsonl`
# PACT Slice 06 — Identity + Manifest + Evidence Bundle

## Date
2026-04-15

This overlay adds:
- widened request/trace identity seed
- telemetry file naming by receipt id
- telemetry manifest/index emission
- provider registry resolution via `provider_ref`
- evidence bundle export for replay/live auditability
- `execute_slice_06`
- `scripts/verify_slice_06.py`
- `harness/regression/slice_06_cases.jsonl`
