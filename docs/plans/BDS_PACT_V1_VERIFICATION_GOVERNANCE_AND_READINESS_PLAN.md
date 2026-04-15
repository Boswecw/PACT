# BDS PACT V1 Verification, Governance, and Readiness Plan

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_VERIFICATION_GOVERNANCE_AND_READINESS_PLAN.md`

---

## Purpose

This document defines the V1 verification posture, threat posture, telemetry posture, readiness gates, and repo-start blockers for PACT V1.

It exists because earlier planning was strong on intent but too weak on enforcement and operational proof.

---

## Core Judgment

PACT V1 must be treated as a **high-impact backend control surface**.

It cannot be accepted on architectural intuition alone.
It must prove:
- packet correctness
- replayability
- safe degradation
- bounded telemetry
- governance enforcement
- rollback ability

---

## V1 Verification Philosophy

### Principle 1 — Replay before optimization
The system must be replayable before it is adaptive.

### Principle 2 — Contracts before throughput
Stage interfaces must be valid before latency optimization work begins.

### Principle 3 — Safe degradation is testable behavior
Fail-closed language without explicit tests is not acceptable.

### Principle 4 — Telemetry is evidence, not authority
Telemetry may inform later decisions but must not directly rewrite runtime behavior in V1.

---

## Phase 0 Deliverables

Before implementation begins, PACT V1 must produce:

1. packet base schema draft
2. packet class schema drafts
3. serialization profile enum
4. safe-failure packet schema
5. runtime receipt schema
6. initial TOON segment registry entries for V1-approved segments
7. deterministic replay harness skeleton
8. starter evaluation corpus
9. degradation matrix
10. threat model draft
11. repository/package boundary decision

If these are not complete, repo work should not begin.

---

## Evaluation Corpus Requirement

V1 cannot defer the eval corpus.

### Required corpus classes
- golden success cases
- golden degraded-but-safe cases
- malformed input cases
- permission-boundary cases
- over-budget cases
- grounding-failure cases
- serialization-mismatch cases
- adversarial retrieval cases

### Required corpus attributes
Each case should retain:
- request input
- source set
- allowed packet class
- expected lineage scope
- expected degradation outcome
- expected packet validity outcome

---

## Deterministic Replay Requirement

For any request_id, the system must be able to replay:
- retrieval inputs
- selected sources
- pruning outcome
- packet assembly inputs
- serialization profile used
- final packet hash
- model-call-allowed decision

Exact byte-equality may not always be required across all stages, but replay must be deterministic enough for regression diagnosis and version comparison.

---

## Required Test Families

### Family 1 — Contract validity tests
Prove that every packet and receipt shape is machine-valid.

### Family 2 — Inter-layer contract tests
Prove that retrieval, pruning, assembly, validation, and cache layers exchange valid payloads.

### Family 3 — Pruning fidelity tests
Prove that required facts and cautions survive allowed pruning.

### Family 4 — Serialization tests
Prove that allowed TOON and JSON segments encode/decode correctly and fail closed on malformed input.

### Family 5 — Degradation tests
Prove that each degradation case results in either:
- degraded but safe packet
- minimum viable packet
- safe-failure packet

### Family 6 — Permission and isolation tests
Prove that permission context and tenant boundaries are preserved across packet, cache, and receipt behavior.

### Family 7 — Replay and rollback tests
Prove that version comparison, replay, and rollback behave predictably.

### Family 8 — Telemetry tests
Prove that telemetry is bounded, classified, and does not leak forbidden content.

### Family 9 — Adversarial tests
Prove resistance to malformed segments, hostile retrieved content, prompt injection carriers, and poisoning candidates.

---

## Threat Posture

PACT V1 requires a formal threat model before code begins.

### Minimum threat classes
1. prompt injection via retrieved content
2. cache poisoning
3. cross-tenant or cross-permission leakage
4. telemetry retention leakage
5. optimization input poisoning
6. malformed TOON or structured segment exploitation
7. unsafe down-classification of sensitive content

### Required rule
Every packet class must declare an **injection boundary posture**.

That means the packet class specification must state:
- what user content may enter
- what retrieved content may enter
- what content must be normalized or blocked
- whether executable or code-like content is allowed

---

## Telemetry Governance Posture

PACT V1 may emit telemetry, but telemetry must remain bounded and privacy-conscious.

### Telemetry allowed in V1
- token counts
- latency breakdown
- degradation state
- cache hit/miss
- packet validation outcomes
- packet class counts
- safe-failure invocation counts
- replay identifiers

### Telemetry not allowed in V1 by default
- raw full user prompts
- raw full packet bodies
- raw internal source excerpts beyond approved retention rules
- freeform operator notes as optimization input

### Hard rule
Telemetry in V1 is for observability and replay support, not direct online learning.

---

## Optimization Posture for V1

PACT V1 does not include live optimization promotion.

### Allowed in V1
- telemetry collection
- replay analysis
- offline proposal drafting
- operator-reviewed findings

### Not allowed in V1
- automatic optimization promotion
- fleet-signal-driven rule changes
- live mutation of packet schemas
- live mutation of serialization profiles

This keeps the learning loop preparatory rather than authoritative.

---

## Readiness Gates

### Gate A — Design readiness
Required before repo work:
- contract family drafts complete
- degradation matrix complete
- threat model draft complete
- repository structure decision complete

### Gate B — Implementation readiness
Required before live integration:
- replay harness working
- starter corpus running
- inter-layer contract tests passing
- safe-failure packet validated

### Gate C — Dogfood readiness
Required before internal traffic:
- runtime receipts emitted
- degradation paths tested
- cache isolation verified
- telemetry minimization rules enforced

### Gate D — Shadow readiness
Required before shadow mode:
- baseline comparison path exists
- latency envelope measured
- token savings measured
- answer-quality regression threshold locked

### Gate E — Limited production readiness
Required before production authority:
- rollback tested
- feature-flag path confirmed
- incident classification and logging confirmed
- safe-failure behavior confirmed in app integration

---

## Repository Start Decision

PACT V1 should not begin runtime coding until Gates A and B blocker artifacts are materially present.

A placeholder repo with no contract or replay foundation is not a valid start.

---

## Final Position

PACT V1 is only worth building if it is easier to verify, replay, and govern than naive prompt assembly.

If the subsystem adds optimization ambition without contract rigor, replayability, and safe degradation, it should not proceed.

