# PACSYSTEM

- Repository: PACT
- Designation: PAC
- Repo class: service / internal runtime
- Canonical artifact path: doc/PACSYSTEM.md
- Build entry: doc/system/BUILD.sh
- Date: 2026-04-15
- Time: 07:58:08 PM America/New_York

---

## 00. Repo Identity

### Purpose
PACT is the packet-and-control contract runtime that provides governed packet shaping, auditability, replay/live execution boundaries, deterministic evidence, and operator-facing export surfaces.

### Canonical identity
- Repository name: `PACT`
- Designation: `PAC`
- Canonical compiled artifact: `doc/PACSYSTEM.md`
- Source tree root: `doc/system/`
- Build entry: `doc/system/BUILD.sh`

### Documentation posture
This repo uses the canonical modular documentation posture where source truth is maintained under `doc/system/` and assembled into `doc/PACSYSTEM.md` through the governed build path.

---

## 01. Scope and Role

PACT is a governed internal runtime/service repo within the Forge workspace.

It currently proves and documents these responsibility areas:
- contract validation
- corpus validation
- runtime execution and degradation handling
- replay/live adapter behavior
- telemetry and evidence emission
- export manifests and replay packages
- control-plane catalog, detail, and handoff
- operator API boundary
- deterministic audit transfer bundles
- run-level indexing and audit packaging
- run-level export summary packaging

PACT is not canonical business truth and is not a generic free-running orchestrator. It is a bounded packet/runtime system with explicit audit and operator surfaces.

---

## 10. Service Contract Surface

### External contract families
PACT owns and enforces machine-readable contract surfaces under `99-contracts/`, including schema validation fixtures and operator-facing request/response shapes.

### Contract responsibilities
- packet schemas and packet-base rules
- runtime receipts
- degradation-state and serialization rules
- grounding and lineage artifacts
- operator API request/response contracts
- export/audit package manifest contracts

### Current proving posture
PACT is green through Slice 12 and has a verification chain that proves compatibility through layered slice verification scripts.

---

## 20. Runtime Topology

### Runtime lanes
Primary runtime ownership is expressed across these repo surfaces:
- `runtime/`
- `control-plane/`
- `adapters/`
- `telemetry/`
- `harness/`
- `scripts/`

### Behavioral posture
PACT executes with fail-closed validation, explicit degradation states, replay/live separation, deterministic artifact writing, and operator-readable evidence.

### Current verified runtime scope
The verified runtime path now includes:
- compile and validation flow
- retrieval and budget handling
- replay/live provider resolution
- telemetry and evidence bundles
- run indexing
- audit transfer packaging
- run export summary packaging

---

## 30. Dependencies

### Runtime dependencies
PACT uses Python runtime dependencies for schema validation and registry-aware reference handling.

Current known required packages for verification include:
- `jsonschema`
- `referencing`

### Local execution posture
Repo-local virtual environment usage is the preferred execution path for deterministic verification on Ubuntu systems that enforce externally managed system Python environments.

Expected local startup:
```bash
cd ~/Forge/ecosystem/pact
source .venv/bin/activate
```

---

## 40. Governance and Controls

### Governance posture
PACT is an internal business system component operating under governance-first design.

### Control expectations
- contract-first development
- deterministic verification
- explicit degradation handling
- evidence over assumption
- bounded operator API actions
- compatibility-sensitive slice layering

### Documentation compliance target
This repo is structured to satisfy the canonical repo documentation posture:
- `doc/system/`
- `doc/system/BUILD.sh`
- repo-class-aware subfolders
- compiled canonical root artifact at `doc/PACSYSTEM.md`

---

## 50. Operations and Verification

### Standard operator workflow
1. enter repo root
2. activate `.venv`
3. run slice verification
4. run mypy
5. rebuild `doc/PACSYSTEM.md` after documentation edits

### Standard verification commands
```bash
python3 scripts/verify_slice_12.py
python3 -m mypy runtime scripts
bash doc/system/BUILD.sh
```

### Expected success state
A healthy repo state for the current slice proves:
- Slice 12 verification passes
- mypy passes
- canonical documentation build succeeds

---

## 99. Appendix — Repo Layout Snapshot

### Major repo areas
- `99-contracts/`
- `corpus/`
- `runtime/`
- `control-plane/`
- `adapters/`
- `telemetry/`
- `harness/`
- `scripts/`
- `docs/`

### Notes
This appendix is intentionally lightweight and should be expanded as the repo documentation system matures.

