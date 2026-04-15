# BDS PACT V1 Master Plan

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_MASTER_PLAN.md`

---

## Purpose

This document defines the executable V1 plan for the **BDS Prompt Assembly and Context Compression (PACT) Submodule**.

PACT is a backend-only subsystem for public-facing applications.
Its job is to improve AI response quality and reduce token waste by producing the **smallest accurate task packet** practical for a given request.

This plan is intentionally narrower than earlier concept drafts.
It absorbs the strongest review-board criticism and removes V1 overreach.

---

## V1 Judgment

The earlier plan was strategically sound but too broad for safe implementation.

V1 must not be a research bundle.
V1 must be a controlled, testable, degradable runtime path with one clear success condition:

**reduce prompt waste and preserve or improve answer quality without creating an operationally brittle or governance-heavy subsystem.**

---

## What V1 Is

PACT V1 is:

- a backend request-path subsystem
- a bounded packet-construction engine
- a deterministic retrieval-to-packet pipeline
- a telemetry-producing runtime
- a dogfood-first internal system that can later support public-fleet learning

PACT V1 is not:

- a user-facing feature
- a full agent memory system
- a full autonomous optimization engine
- a broad context-folding runtime
- a self-modifying prompt framework

---

## V1 Scope Lock

### In scope

1. one runtime request path
2. one minimum viable packet contract family
3. hybrid retrieval
4. reranking
5. hierarchical pruning
6. deterministic packet assembly
7. input-side selective TOON serialization for structured repetitive packet segments only
8. grounding support
9. cache and freshness controls
10. telemetry and replay receipts
11. safe degradation and fallback behavior

### Explicitly deferred from V1

1. context folding
2. recursive branch memory
3. DSPy auto-optimization in production runtime
4. fleet-driven optimization promotion
5. model-generated TOON output
6. broad packet-class expansion
7. multi-app custom packet dialects
8. autonomous learning-rule updates

---

## Primary Objectives

### Objective 1 — Token reduction

Reduce final prompt size materially versus naive retrieval-plus-prompt baseline.

### Objective 2 — Accuracy preservation or improvement

Preserve or improve grounded answer quality on the V1 evaluation corpus.

### Objective 3 — Deterministic replayability

Any request processed through PACT V1 must be replayable from retained runtime receipts and packet lineage.

### Objective 4 — Safe degradation

If one or more layers fail, the application must degrade predictably rather than collapse or silently produce weak packets.

### Objective 5 — Future optimization readiness

V1 must emit the telemetry and replay artifacts needed for later optimization work without making optimization part of the live critical path.

---

## Core Architectural Decision

PACT V1 uses a **data-plane / control-plane split**.

### Data plane
The live request path that constructs packets for model calls.

### Control plane
Offline and governed activities such as:
- eval corpus execution
- replay analysis
- packet-quality review
- optimization proposal generation
- rollout and rollback decisions

Hard rule:
V1 optimization logic must not sit inside the live request path.

---

## V1 Runtime Path

The runtime path is:

1. request intake
2. source and permission check
3. retrieval
4. rerank
5. hierarchical pruning
6. packet assembly
7. optional TOON serialization for approved structured segments
8. packet validation
9. grounding support attachment
10. cache write/read behavior
11. model call
12. runtime receipt emission

Hard rule:
If packet validation fails, the packet must not proceed to model call.

---

## Minimum Viable Packet Contract Family

V1 supports only these packet classes:

1. `answer_packet`
2. `policy_response_packet`
3. `search_assist_packet`

`workflow_guidance_packet` is deferred unless needed by the first dogfood app.

Each packet class must inherit from a shared packet base contract.

---

## TOON Decision for V1

TOON is retained in V1 only under a narrow posture.

### Allowed in V1
- input-side serialization for structured repetitive packet segments
- ranked result rows
- evidence tables
- compact metadata bundles

### Not allowed in V1
- model-generated TOON output
- TOON as a replacement for full packet schema
- TOON for long instruction prose
- TOON before retrieval and pruning are complete

Hard rule:
TOON is an optional segment-level transport optimization, not a first-class truth layer.

---

## Safe Degradation Requirement

PACT V1 must define a **minimum viable packet** and a **safe-failure packet**.

### Minimum viable packet
A reduced packet produced when one or more optimization layers are unavailable but core answering may still proceed safely.

### Safe-failure packet
A bounded packet that explicitly prevents unsafe model use and hands control back to the application with a deterministic failure state.

Hard rule:
Fail-closed behavior without a safe-failure packet is not acceptable for V1.

---

## Dogfooding Sequence

### Stage 1 — Internal dogfooding only
PACT V1 runs behind one BDS-owned application first.

### Stage 2 — Shadow mode on real traffic
PACT V1 runs in parallel without production authority.

### Stage 3 — Limited production authority
PACT V1 serves a bounded share of production traffic behind feature flags.

No broad public-fleet optimization behavior is allowed in V1.

---

## Hard Blockers Before Code Begins

1. packet base schema locked
2. packet class schemas locked
3. serialization profile enum locked
4. degradation matrix locked
5. safe-failure packet contract locked
6. replay receipt schema locked
7. telemetry event schema locked
8. evaluation corpus and replay harness started
9. threat model drafted
10. repository/package boundaries locked

---

## Acceptance Gate for V1

PACT V1 is not implementation-ready until the blocker set above is complete.

PACT V1 is not production-ready until all of the following are demonstrated:

1. token reduction is material versus baseline
2. answer quality is equal or better on the V1 corpus
3. replay is deterministic enough for debugging and regression work
4. degradation paths work under forced failures
5. safe-failure packet behavior is proven
6. cache behavior is isolated and freshness-aware
7. telemetry is bounded and privacy-safe

---

## Final Position

PACT V1 should be built as a **small, deterministic, degradable, packet-first backend subsystem**.

V1 succeeds if it becomes:
- cheaper than naive prompting
- safer than naive prompting
- more replayable than naive prompting
- easier to improve later without live-path instability

V1 fails if it tries to absorb the full research landscape before the core packet pipeline is proven.

