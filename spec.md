# spec.md

## Title
Hermes + OpenClaw Phase 0 — Decision Lock Acceptance

## Goal
Create the written acceptance artifacts that freeze authority, proving-slice choice, and repo split before implementation begins.

## Why this slice exists
The implementation plan is explicitly phase-gated.

Phase 0 must be accepted in writing before package skeleton work, contract work, runtime adapter work, or OpenClaw control-plane work begins.

## In-scope
- written authority acceptance
- written proving-slice acceptance
- written repo-split acceptance
- a bounded verification gate that proves the acceptance file exists and contains the required decision markers

## Out of scope
- package creation
- schema changes
- adapter code
- runtime state machine changes
- OpenClaw screens or API flows
- proving-slice code
- scheduling
- replay
- hardening

## Locked decisions
1. There is no master orchestrator above YellowJacket.
2. YellowJacket remains the sole runtime admission point.
3. OpenClaw requests are intents, not execution commands.
4. Hermes executes only YellowJacket-issued invocation packets and returns receipts/results.
5. OpenClaw may never dispatch execution directly to Hermes.
6. Hermes does not own schedule validity, replay admission, approvals, or direct app writeback.
7. Memory is disabled in v1.
8. Subagents are forbidden in v1.
9. The first Hermes/OpenClaw proving slice is `documentation-drift-digest`.
10. Repo split is:
   - YellowJacket: contracts, runtime, admission, normalization, verification integration
   - Hermes: standalone execution provider runtime
   - OpenClaw: standalone operator/control plane

## Deliverables
- `spec.md`
- `todo.md`
- `docs/implementation/hermes_openclaw/phase_0_acceptance.md`
- `tests/phase_0_gate.sh`

## Verification
### Artifact checks
Prove the slice by verifying:
- all required files exist
- acceptance markers are present
- the proving slice is `documentation-drift-digest`
- repo split markers are present
- authority markers match the locked decisions

### Exact verification command

```bash
bash tests/phase_0_gate.sh
```

### Passing condition
The verification script prints:

```text
PHASE_0_GATE_PASS
```

### Failing condition
Any missing file, missing marker, or authority drift causes a non-zero exit and prints the missing requirement.

## Exit rule
Do not start Phase 1 until this slice is applied, reviewed, and the verification gate passes.
