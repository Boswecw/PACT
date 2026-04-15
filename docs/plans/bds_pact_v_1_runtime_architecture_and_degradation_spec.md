# BDS PACT V1 Runtime Architecture and Degradation Specification

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_RUNTIME_ARCHITECTURE_AND_DEGRADATION_SPEC.md`

---

## Purpose

This document defines the runtime path, component boundaries, latency posture, and degradation behavior for PACT V1.

It exists because the earlier plan described layers but did not define operational behavior under success, partial failure, or total failure.

---

## Architectural Principle

PACT V1 must be architected as a **degradable deterministic pipeline**, not as a research stack where all layers must succeed simultaneously.

The runtime must always know:
- what failed
- whether fallback is allowed
- whether a minimum viable packet may still be produced
- whether a safe-failure packet must be returned instead

---

## Component Model

PACT V1 runtime consists of six components.

### 1. Intake Gate
Responsibilities:
- validate request shape
- validate consumer identity
- validate permission context
- assign request_id and trace_id

### 2. Retrieval Engine
Responsibilities:
- execute approved retrieval methods
- return candidate source objects with source refs and permission boundaries

### 3. Rerank and Pruning Engine
Responsibilities:
- rerank retrieved objects
- apply hierarchical pruning
- enforce token-budget pre-assembly thresholds

### 4. Packet Compiler
Responsibilities:
- construct packet from surviving material
- choose serialization profile
- attach structured TOON segments only when allowed

### 5. Packet Validator and Grounding Support Builder
Responsibilities:
- validate packet schema
- validate segment profiles
- attach grounding support references and excerpts
- reject invalid or unsafe packets

### 6. Cache and Receipt Layer
Responsibilities:
- manage read/write caching behavior
- attach lineage metadata
- emit runtime receipts and metrics

---

## Control Plane Separation

The following are not part of the runtime request path:
- optimization proposals
- eval corpus execution
- replay comparison jobs
- packet quality review
- promotion or rollback decisions

These belong to the control plane only.

---

## Runtime Request Path

1. request received
2. intake gate validates request
3. retrieval engine gathers candidates
4. rerank and pruning engine narrows candidates
5. packet compiler builds packet
6. packet validator validates packet
7. grounding support is attached
8. cache layer records or reuses allowed content
9. model call proceeds only if packet is admissible
10. runtime receipt emitted

---

## Latency Budget Posture

PACT V1 must not be allowed to become an invisible latency amplifier.

### Required budgeting model
Each packet class must carry:
- max runtime overhead budget
- max retrieval budget
- max rerank/pruning budget
- max packet compile/validation budget

### Hard rule
If the packet path cannot complete within class-defined limits, the system must degrade rather than continue consuming request time indefinitely.

Exact numeric budgets are a blocker item to be locked before implementation begins.

---

## Degradation Matrix

### Case A — Retrieval degraded but not failed
Examples:
- one retrieval backend unavailable
- lexical retrieval available, vector retrieval unavailable

Allowed behavior:
- continue with reduced retrieval mode if permission and quality rules permit
- emit degraded runtime receipt

### Case B — Reranker unavailable
Allowed behavior:
- continue with retrieval-only ordering if allowed for that packet class
- mark packet as degraded
- apply stricter token cap and fewer candidates

### Case C — Pruning engine unavailable
Allowed behavior:
- attempt minimum viable packet path only if pre-pruning candidate set fits class budget
- otherwise return safe-failure packet

### Case D — Packet compiler failure
Allowed behavior:
- no model call
- return safe-failure packet
- emit compiler_failure receipt

### Case E — Packet validation failure
Allowed behavior:
- no model call
- return safe-failure packet
- emit validation_failure receipt

### Case F — TOON segment validation failure
Allowed behavior:
- remove TOON segment and retry compile only if packet class allows non-TOON fallback
- otherwise safe-failure packet

### Case G — Grounding support build failure
Allowed behavior:
- packet may proceed only if packet class allows answering without grounding support
- otherwise safe-failure packet

### Case H — Cache unavailable
Allowed behavior:
- continue uncached
- emit cache_degraded receipt

---

## Minimum Viable Packet Rules

A minimum viable packet is allowed only when:
- packet class explicitly permits degraded answering
- permission boundaries remain intact
- source lineage remains attached
- packet still validates
- token budget remains within class limit

A minimum viable packet must not:
- hide degraded state from runtime receipts
- bypass validation
- bypass sensitivity rules

---

## Safe-Failure Packet Rules

Safe-failure packet exists to prevent unsafe or inconsistent model use.

It must contain:
- request_id
- packet_class
- failure_state
- retry_allowed flag
- operator_trace_ref
- no user-sensitive internals

The application may map this to a generic failure path, but the runtime receipt must preserve precise technical cause.

---

## Cache Model

### Cache layers allowed in V1
1. packet cache
2. structured segment cache for approved serialized regions
3. stable prefix cache where provider/runtime supports it

### Cache key minimums
Cache keys must include:
- packet class
- source lineage digest
- permission context
- serialization profile
- version set

### Hard rule
Cache reuse must never cross permission or tenant boundary.

---

## Replay and Receipt Model

Every runtime request must emit a receipt with enough data to support replay and regression analysis.

Minimum receipt fields:
- request_id
- trace_id
- packet_class
- version_set
- retrieval mode used
- pruning mode used
- serialization profile
- degraded flags
- source lineage digest
- token counts
- latency breakdown
- final packet hash
- model call allowed boolean

---

## Operational Failure Policy

PACT V1 must fail in one of three explicit ways:

1. degraded but safe
2. minimum viable packet allowed
3. safe-failure packet returned

Silent weak-packet continuation is forbidden.

---

## Execution Prerequisites

Before code begins, this document requires:
- per-packet-class latency budgets
- allowed degradation states by packet class
- safe-failure packet schema
- receipt schema
- cache key contract
- lineage digest method

---

## Final Position

PACT V1 runtime architecture is acceptable only if it can continue safely under partial failure and explain every degraded path through runtime receipts.

If every layer must succeed perfectly for the system to function, the architecture is not ready.

