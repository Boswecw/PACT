# BDS PACT V1 Packet and Serialization Contract Lock

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_PACKET_AND_SERIALIZATION_CONTRACT_LOCK.md`

---

## Purpose

This document locks the V1 contract posture for packets, serialization profiles, safe-failure behavior, and runtime receipts.

It exists because earlier planning described packet ideas but did not define sufficiently rigid contracts for safe implementation.

---

## Core Judgment

PACT V1 cannot be implemented safely without machine-readable contracts.

Packet classes, serialization profiles, runtime receipts, and safe-failure payloads must be treated as governed contract surfaces before runtime code begins.

---

## Contract Families Required in V1

### Family A — Packet Base Contract
Shared fields required for all packet classes.

### Family B — Packet Class Contracts
V1 packet classes only.

### Family C — Segment Serialization Contracts
Defines when plain text, JSON, TOON, or compact bounded fields are allowed.

### Family D — Safe-Failure Packet Contract
Defines deterministic failure payload for the application path.

### Family E — Runtime Receipt Contract
Defines replay, trace, and metrics payload emitted by the runtime.

### Family F — Negative Constraint Contract
Defines normalized operator-accepted failure or rejection reason classes for later controlled optimization work.

---

## Packet Base Contract

Every packet must include at minimum:
- `schema_version`
- `packet_id`
- `packet_class`
- `packet_revision`
- `request_id`
- `trace_id`
- `consumer_identity`
- `permission_context_digest`
- `source_lineage_digest`
- `serialization_profile`
- `lifecycle_state`
- `freshness_state`
- `admissibility_state`
- `created_at`
- `expires_at`
- `packet_hash`
- `grounding_required`
- `warnings[]`
- `restrictions[]`

Hard rule:
No packet may proceed to model call without a valid packet base envelope.

---

## V1 Packet Classes

### 1. `answer_packet`
Use for direct grounded answer tasks.

Required class fields:
- `task_goal`
- `instruction_block`
- `support_blocks[]`
- `grounding_refs[]`
- `answer_constraints[]`

### 2. `policy_response_packet`
Use for policy, eligibility, or boundary-sensitive responses.

Required class fields:
- `policy_scope`
- `policy_statements[]`
- `required_cautions[]`
- `grounding_refs[]`
- `disallowed_answer_modes[]`

### 3. `search_assist_packet`
Use for ranked discovery assistance.

Required class fields:
- `search_goal`
- `ranked_result_blocks[]`
- `selection_constraints[]`
- `grounding_refs[]`
- `result_count`

`workflow_guidance_packet` remains deferred unless separately unlocked.

---

## Serialization Profile Enum

V1 allowed serialization profiles:
- `plain_text_only`
- `plain_text_with_compact_fields`
- `plain_text_with_json_segment`
- `plain_text_with_toon_segment`

Hard rule:
The serialization profile is a governed enum.
No ad hoc profile variants are allowed in V1.

---

## Serialization Rules

### Plain text
Allowed for:
- instruction prose
- policy nuance
- answer framing
- constraints that rely on natural-language fidelity

### Compact fields
Allowed for:
- bounded metadata slots
- fixed short values
- class-level flags and identifiers

### JSON segment
Allowed for:
- small structured segments where interoperability matters more than token reduction

### TOON segment
Allowed for:
- repetitive structured rows
- ranked result rows
- evidence tables
- metadata bundles with repeated field names

Not allowed for:
- long prose
- full packet body
- raw source dumps
- pre-pruning candidate sets

---

## TOON Lock for V1

TOON in V1 is input-side only.

### Allowed TOON use
- packet segment serialization after selection and pruning
- model input only

### Forbidden TOON use in V1
- model output contract
- canonical persistence format
- replacement for packet schema
- freeform TOON variant dialects

### TOON segment requirements
Each TOON segment must carry:
- `segment_id`
- `segment_version`
- `row_definition_id`
- `row_count`
- `source_lineage_digest`
- `segment_hash`

### Validation rule
Malformed TOON segment means:
- segment rejected
- compile retry allowed only if packet class permits fallback profile
- otherwise safe-failure packet

---

## Safe-Failure Packet Contract

Safe-failure packet must include:
- `schema_version`
- `failure_packet_id`
- `request_id`
- `trace_id`
- `packet_class`
- `failure_state`
- `retry_allowed`
- `operator_trace_ref`
- `public_reason_code`

Forbidden in safe-failure packet:
- raw internal error text
- source excerpts
- serialized structured payloads
- internal schema internals

---

## Runtime Receipt Contract

Runtime receipt must include:
- `schema_version`
- `receipt_id`
- `request_id`
- `trace_id`
- `packet_id`
- `packet_class`
- `version_set`
- `retrieval_mode`
- `pruning_mode`
- `serialization_profile`
- `degradation_state`
- `source_lineage_digest`
- `packet_hash`
- `token_counts`
- `latency_breakdown`
- `model_call_allowed`
- `safe_failure_invoked`

---

## Negative Constraint Contract

Negative constraints are not freeform memory.
They are normalized governed records.

Required fields:
- `constraint_id`
- `packet_class`
- `constraint_type`
- `reason_code`
- `created_at`
- `source_review_ref`
- `active`
- `superseded_by`

Starter reason codes:
- `missing_grounding_support`
- `dropped_required_caution`
- `over_budget_packet`
- `irrelevant_context_preserved`
- `unsafe_policy_simplification`
- `serialization_mismatch`
- `packet_validation_failure`

Hard rule:
V1 must cap active negative constraints per packet class.
This avoids rule-soup accumulation.

---

## Versioning Rules

Every contract family must carry:
- explicit `schema_version`
- immutable identifier
- compatibility posture

Compatibility postures:
- `compatible`
- `migration_required`
- `incompatible`

No silent schema drift is allowed.

---

## Required Machine-Readable Outputs Before Code

Before runtime code begins, BDS must produce machine-readable definitions for:
- packet base schema
- answer_packet schema
- policy_response_packet schema
- search_assist_packet schema
- safe-failure packet schema
- runtime receipt schema
- negative constraint schema
- serialization profile enum
- TOON segment definition registry entries for approved V1 segments

---

## Final Position

PACT V1 contracts must be locked before runtime work.

Without these contracts, the subsystem will drift into implicit interfaces, weak validation, and ungoverned serialization behavior.

