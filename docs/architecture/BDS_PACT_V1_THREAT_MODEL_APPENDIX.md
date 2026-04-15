# BDS PACT V1 Threat Model Appendix

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_THREAT_MODEL_APPENDIX.md`

---

## Purpose

This appendix defines the minimum V1 threat posture for PACT.

It is intentionally narrow and implementation-relevant.
It exists to prevent the runtime from being treated as a token-optimization subsystem only, when it is actually a high-impact prompt and context control surface.

---

## Core Rule

PACT V1 must not proceed into runtime coding until each V1 packet class has:
- a trust-boundary statement
- an injection-boundary statement
- a minimum mitigation posture
- at least one corresponding adversarial test class

---

## Trust Boundary Model

PACT V1 sits between:

1. inbound request and user content
2. retrieved source material
3. structured packet construction
4. model-call admission
5. telemetry and replay retention

This means the system must defend not only against bad outputs, but against poisoned inputs, malformed segments, boundary drift, and unsafe retention.

---

## Minimum Threat Classes

### Threat 1 — Prompt injection via retrieved content
Risk:
Hostile or malformed retrieved content attempts to override packet instructions or alter model behavior.

Required mitigation:
- retrieved content treated as content, not instruction authority
- packet class defines what retrieved content may enter support blocks
- adversarial retrieval corpus cases required

### Threat 2 — Cache poisoning
Risk:
A stale or malicious cached segment is reused under the wrong lineage or permission boundary.

Required mitigation:
- cache keys include permission context and source lineage digest
- cache reuse never crosses permission boundary
- cache mismatch tests required

### Threat 3 — Cross-tenant or cross-permission leakage
Risk:
A packet, cached segment, or receipt exposes data outside the allowed consumer boundary.

Required mitigation:
- permission context digest required in packet envelope and cache key
- permission-boundary corpus cases required
- telemetry must not retain raw packet bodies by default

### Threat 4 — Telemetry retention leakage
Risk:
Telemetry retains more user or source content than allowed.

Required mitigation:
- telemetry allow-list only
- explicit forbidden retention list
- 30-day default retention
- replay exceptions require flagged purpose

### Threat 5 — Optimization input poisoning
Risk:
Incident or fleet signals later used for optimization are manipulated or biased, producing harmful proposal candidates.

Required mitigation:
- V1 telemetry is evidence only, not authority
- negative constraints must be normalized records, not raw freeform memory
- optimization not in live path for V1

### Threat 6 — Malformed TOON or structured segment exploitation
Risk:
Malformed segment payloads trigger decoder errors, validation bypasses, or unsafe fallback behavior.

Required mitigation:
- TOON segments validated strictly
- malformed segment causes fallback or safe-failure only by contract
- no model-generated TOON output in V1

### Threat 7 — Unsafe down-classification of sensitive content
Risk:
Content is incorrectly marked public-safe and efficiently delivered downstream.

Required mitigation:
- sensitivity posture checked independently of retrieval classification
- policy-sensitive packets require explicit grounding and caution rules
- sensitivity filter run before final model-call admission

---

## Packet-Class Injection Boundary Declarations

### `answer_packet`
Allowed inbound content:
- user request text
- approved retrieved support blocks
- bounded structured result segments

Forbidden inbound content:
- executable instruction override content from retrieved sources
- raw hidden system directives embedded in support blocks

### `policy_response_packet`
Allowed inbound content:
- approved policy statements
- required cautions
- grounded support refs

Forbidden inbound content:
- user-supplied policy text treated as authority
- unverified policy summaries treated as canonical

### `search_assist_packet`
Allowed inbound content:
- ranked structured results
- selection constraints
- approved metadata bundles

Forbidden inbound content:
- cached result sets across permission boundary
- ad hoc row definitions not in TOON registry

---

## Output Sanitization Rule

PACT V1 governs input assembly, but output must still be treated as untrusted until checked by app-level or downstream response policy.

Minimum rule:
PACT V1 must not claim that packet correctness alone guarantees safe model output.

Where policy requires, downstream output filtering or validation remains mandatory.

---

## Threat-to-Test Mapping

| Threat | Minimum Required Test |
|---|---|
| Prompt injection via retrieved content | adversarial retrieval corpus case |
| Cache poisoning | cache key isolation test |
| Cross-permission leakage | permission-boundary replay test |
| Telemetry leakage | telemetry allow-list validation test |
| Optimization input poisoning | negative-constraint normalization test |
| Malformed TOON | strict decode failure test |
| Sensitive down-classification | sensitivity filter regression test |

---

## Required Review Triggers

The following changes require threat-model review update:
- new packet class
- new serialization profile
- new cache layer
- new retained telemetry field
- allowing model-generated structured output
- changing permission or sensitivity logic

---

## Final Position

PACT V1 is not just a packet optimizer.
It is a trust-boundary system.

If the threat posture is not explicit and test-linked, the runtime will optimize unsafe behavior faster instead of making the application safer.

