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
