# BDS PACT V1 Repo Skeleton and Ownership Map

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_REPO_SKELETON_AND_OWNERSHIP_MAP.md`

---

## Purpose

This document defines the minimum acceptable repository structure and ownership boundaries for PACT V1.

It exists because the earlier planning set was strong conceptually but too vague about package separation, control-artifact location, and how to prevent research, runtime, and governance concerns from collapsing into one unmaintainable code surface.

---

## Core Rule

PACT V1 must not begin as a single undifferentiated code directory.

Contracts, corpus, harness, runtime code, and docs must be separated from the beginning.

---

## Minimum Acceptable Repo Skeleton

```text
pact/
├── 99-contracts/
│   ├── schemas/
│   ├── fixtures/
│   │   ├── valid/
│   │   ├── invalid/
│   │   └── edge/
│   └── registry/
│
├── corpus/
│   ├── corpus_manifest.json
│   ├── cases/
│   └── sources/
│
├── harness/
│   ├── replay/
│   ├── regression/
│   └── adversarial/
│
├── runtime/
│   ├── intake/
│   ├── retrieval/
│   ├── pruning/
│   ├── compiler/
│   ├── validation/
│   ├── cache/
│   └── receipts/
│
├── telemetry/
│   ├── contracts/
│   ├── retention/
│   └── exporters/
│
├── control-plane/
│   ├── analysis/
│   ├── proposals/
│   └── rollout/
│
├── adapters/
│   ├── app_adapters/
│   └── provider_adapters/
│
├── docs/
│   ├── plans/
│   ├── architecture/
│   └── runbooks/
│
└── src/
    └── shared/
```

---

## Boundary Rules

### `99-contracts/`
Owns:
- machine-readable schemas
- enum definitions
- TOON segment registry entries
- valid/invalid fixtures

Hard rule:
No runtime module may define packet structure privately outside the contract bundle.

### `corpus/`
Owns:
- starter eval corpus
- corpus manifest
- source-set references

Hard rule:
Production telemetry must not be dropped directly into corpus without review and redaction.

### `harness/`
Owns:
- replay harness
- regression harness
- adversarial tests

Hard rule:
Replay and regression logic must not be buried inside runtime modules.

### `runtime/`
Owns:
- live request path only

Hard rule:
No optimization proposal generation inside runtime path.

### `telemetry/`
Owns:
- telemetry contracts
- retention rules
- exporters and bounded metrics logic

Hard rule:
Telemetry must respect allow-list governance and must not privately define extra retained fields.

### `control-plane/`
Owns:
- offline analysis
- proposal drafting
- rollout and rollback support artifacts

Hard rule:
Control-plane outputs do not gain production authority without explicit promotion flow.

### `adapters/`
Owns:
- app-specific adapters
- provider-specific adapters

Hard rule:
App-specific behavior must not leak into core runtime logic.

### `docs/`
Owns:
- planning docs
- architecture docs
- runbooks

### `src/shared/`
Owns:
- shared utilities that are truly common and non-domain-specific

Hard rule:
Do not turn `shared/` into a dumping ground.

---

## Ownership Map

Because BDS is single-operator, “ownership” in V1 means **responsibility boundary**, not different people.

### Contract owner boundary
Responsible for:
- schema changes
- enum changes
- fixture validity
- compatibility posture

### Runtime owner boundary
Responsible for:
- intake, retrieval, pruning, compile, validation, cache, receipts
- adherence to budgets and degradation rules

### Harness owner boundary
Responsible for:
- replay reliability
- regression coverage
- adversarial testing

### Control-plane owner boundary
Responsible for:
- analysis jobs
- proposal drafting
- rollout/rollback artifact generation

### Telemetry owner boundary
Responsible for:
- allow-list enforcement
- retention discipline
- metrics correctness

### Adapter owner boundary
Responsible for:
- app integration behavior
- provider integration behavior
- preventing special-case creep into runtime core

---

## Repo Start Rule

An acceptable repository start is only one that contains at minimum:

- `99-contracts/`
- `corpus/`
- `harness/`
- `runtime/`
- `docs/`

A placeholder runtime repo with no contract, corpus, or harness foundation is not a valid V1 start.

---

## App Adapter Rule

Each public-facing application must integrate with PACT through an adapter boundary.

Allowed app-specific concerns:
- request mapping
- response mapping
- packet-class choice where policy allows
- feature flag integration

Forbidden app-specific concerns in core runtime:
- custom packet dialects
- packet field mutation
- app-specific cache-key logic
- app-specific serialization-profile variants

---

## Version-Control Rule for Accepted Changes

Any accepted change to:
- packet contracts
- enum sets
- TOON registry entries
- evaluation corpus manifest
- degradation matrix
- promotion-ready optimizer proposal artifacts

must result in an explicit version-controlled change, not only a runtime database state mutation.

---

## Immediate Next Actions

1. create repo skeleton exactly or very close to the structure above
2. populate `99-contracts/` before `runtime/` implementation work
3. create starter `corpus/` and `harness/` placeholders before request-path code
4. place the existing V1 plan documents into `docs/plans/`

---

## Final Position

PACT V1 will fail into sprawl unless repository boundaries are defined before implementation.

The repo skeleton is not housekeeping.
It is part of the control surface.

