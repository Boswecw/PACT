# BDS PACT V1 Quantitative Budget Lock

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_QUANTITATIVE_BUDGET_LOCK.md`

---

## Purpose

This document locks the initial quantitative budgets for PACT V1.

These values are V1 planning defaults and must be revisited with dogfooding evidence.
They exist now because earlier plan versions left all numeric decisions implicit, which would have forced the first implementation to invent policy in code.

---

## Core Rule

PACT V1 runtime must operate within explicit time and token budgets by packet class.

If the pipeline cannot satisfy the class budget, it must degrade or fail safely rather than silently overrunning cost or latency expectations.

---

## Budget Philosophy

V1 budgets must be:
- conservative enough to control latency
- loose enough to allow dogfood learning
- easy to measure in runtime receipts
- strict enough to trigger degradation when exceeded

These are not final forever numbers.
They are V1 lock values for initial implementation and dogfood proof.

---

## Packet-Class Runtime Budgets

| Packet Class | Max Retrieval (ms) | Max Rerank + Prune (ms) | Max Compile + Validate (ms) | Max PACT Overhead (ms) | Max Input Token Budget | Min Required Reduction vs Naive Baseline |
|---|---:|---:|---:|---:|---:|---:|
| `answer_packet` | 350 | 250 | 150 | 750 | 3500 | 35% |
| `policy_response_packet` | 300 | 200 | 150 | 650 | 3000 | 25% |
| `search_assist_packet` | 400 | 300 | 175 | 875 | 4200 | 35% |

### Notes
- `Max PACT Overhead` excludes downstream model generation latency and measures only the PACT request path overhead.
- If any stage budget is exceeded, the runtime must follow the degradation matrix.

---

## Safe-Failure Trigger Rules

A safe-failure packet must be returned when any of the following occurs:

1. packet validation fails
2. required grounding support cannot be attached for a packet class that requires it
3. permission context is unresolved or inconsistent
4. token budget cannot be satisfied after allowed degradation steps
5. compile retry after TOON fallback still fails

---

## Minimum Viable Packet Budget Rules

A minimum viable packet may be attempted only when:
- the packet class explicitly allows degraded answering
- the surviving context remains within 80% of the class input-token budget before final compile
- required source lineage and permission context remain intact

If not, the system must return safe-failure rather than continue compressing blindly.

---

## Quality Gates for Quantitative Success

PACT V1 does not succeed on token reduction alone.

### Dogfood success thresholds
- average token reduction: **>= 35%** for `answer_packet` and `search_assist_packet`
- average token reduction: **>= 25%** for `policy_response_packet`
- grounded-answer quality regression: **<= 2%** against the locked eval corpus
- safe-failure false-positive rate: **<= 1%** on the eval corpus
- replay success rate: **>= 99%** for retained receipts on the dogfood corpus

### Shadow-mode gate
Before limited production authority, shadow-mode evidence must show:
- average token reduction: **>= 30%**
- grounded-answer quality regression: **<= 1.5%**
- no critical permission-boundary violations
- no cache cross-boundary incidents
- no serialization-profile mismatch incidents classified as high severity

---

## Cache Budgets

### Packet cache
- target hit rate after stable dogfood usage: **>= 20%** for repeated query families
- cache lookup budget: **<= 20 ms**

### Structured segment cache
- target hit rate after stable dogfood usage: **>= 30%** for repeated result families where allowed
- segment read budget: **<= 15 ms**

### Stable prefix cache
- target enabled only where provider/runtime supports it
- no provider-dependent numeric guarantee is assumed in V1 runtime policy

---

## Telemetry Retention Budgets

V1 telemetry retention defaults:
- standard runtime telemetry: **30 days**
- replay-analysis flagged receipts: **90 days** maximum
- raw packet bodies: **not retained by default**

Hard rule:
Telemetry retained beyond the default must require explicit flagged purpose tied to replay or incident analysis.

---

## Negative Constraint Budget

Maximum active negative constraints per packet class: **12**.

At or above this threshold:
- no new active constraint may be added without supersession or retirement review
- packet-class rule review is required

This prevents rule accumulation from turning the compiler into an unmaintainable exception engine.

---

## Degradation Retry Limits

### Allowed compile retries
- max one retry after TOON-segment fallback
- no more than one budget-reduction retry for minimum viable packet path

### Forbidden
- unbounded repeated pruning passes
- recursive budget shrinking loops
- hidden retry chains not reflected in runtime receipts

---

## Required Runtime Receipt Metrics

Each runtime receipt must include enough quantitative data to test this document.

Required:
- retrieval latency
- rerank/prune latency
- compile/validate latency
- total PACT overhead
- final input token count
- naive baseline token estimate
- reduction percentage
- degradation state
- cache hit/miss state

---

## Review Rule

These budgets are locked for V1 implementation start but must be reviewed after:
- first 25 dogfood corpus cases
- first 100 shadow-mode requests
- first limited-production review window

Budget changes must be explicit revision-controlled changes, not live tuning.

---

## Final Position

PACT V1 cannot claim control over cost or latency without explicit numeric budgets.

These values are the initial lock set.
If implementation cannot live inside them, the design must be revised rather than silently stretched.

