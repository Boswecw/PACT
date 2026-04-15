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
