# BDS PACT V1 Schema Lock Pack

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_SCHEMA_LOCK_PACK.md`

---

## Purpose

This document converts the earlier packet-and-serialization contract posture into a concrete schema-lock plan.

It is not the final machine-readable schema bundle.
It is the governing artifact that defines exactly which schema files must exist before runtime code begins, what each schema must own, and what example fixtures must accompany them.

---

## Core Rule

PACT V1 runtime coding must not begin until the schema bundle below exists in machine-readable form and is validated by example fixtures.

---

## Required Schema Bundle

The V1 schema bundle must contain these files.

### Packet contracts
1. `packet_base.schema.json`
2. `answer_packet.schema.json`
3. `policy_response_packet.schema.json`
4. `search_assist_packet.schema.json`
5. `safe_failure_packet.schema.json`

### Runtime and governance contracts
6. `runtime_receipt.schema.json`
7. `negative_constraint.schema.json`
8. `serialization_profile_enum.schema.json`
9. `degradation_state_enum.schema.json`
10. `version_set.schema.json`

### Segment and registry contracts
11. `toon_segment.schema.json`
12. `toon_segment_registry_v1.schema.json`
13. `grounding_ref.schema.json`
14. `source_lineage_digest.schema.json`
15. `cache_manifest_entry.schema.json`

---

## Required Fixture Bundle

Each required schema must ship with:

- one valid example fixture
- one invalid example fixture
- one edge-case fixture where applicable

Minimum fixture paths:

```text
contracts/
  schemas/
  fixtures/
    valid/
    invalid/
    edge/
```

---

## Packet Base Required Fields

The machine-readable `packet_base.schema.json` must enforce at minimum:

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
All packet-class schemas must compose the packet base rather than re-declare it inconsistently.

---

## Packet-Class Required Fields

### `answer_packet`
Must require:
- `task_goal`
- `instruction_block`
- `support_blocks[]`
- `grounding_refs[]`
- `answer_constraints[]`

### `policy_response_packet`
Must require:
- `policy_scope`
- `policy_statements[]`
- `required_cautions[]`
- `grounding_refs[]`
- `disallowed_answer_modes[]`

### `search_assist_packet`
Must require:
- `search_goal`
- `ranked_result_blocks[]`
- `selection_constraints[]`
- `grounding_refs[]`
- `result_count`

---

## Serialization Profile Enum Lock

V1 allowed serialization profiles are only:

- `plain_text_only`
- `plain_text_with_compact_fields`
- `plain_text_with_json_segment`
- `plain_text_with_toon_segment`

No other serialization profile is allowed in V1.

---

## Degradation State Enum Lock

V1 degradation states must be an enum, not free text.

Starter values:
- `normal`
- `retrieval_degraded`
- `rerank_degraded`
- `pruning_degraded`
- `cache_degraded`
- `minimum_viable_packet`
- `safe_failure`

These may be refined before schema finalization, but they must be locked before runtime coding begins.

---

## TOON Segment Contract Lock

The `toon_segment.schema.json` must require at minimum:

- `segment_id`
- `segment_version`
- `row_definition_id`
- `row_count`
- `source_lineage_digest`
- `segment_hash`
- `toon_payload`

### V1 TOON rules
- input-side only
- no model-generated TOON output contract in V1
- no canonical persistence as TOON
- no raw source dump serialization

### Registry requirement
The `toon_segment_registry_v1.schema.json` must define the approved row definitions for V1 segments.
No ad hoc row definition is allowed.

---

## Runtime Receipt Contract Lock

The `runtime_receipt.schema.json` must require:

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

## Negative Constraint Contract Lock

The `negative_constraint.schema.json` must require:

- `constraint_id`
- `packet_class`
- `constraint_type`
- `reason_code`
- `created_at`
- `source_review_ref`
- `active`
- `superseded_by`

### Starter reason-code enum
- `missing_grounding_support`
- `dropped_required_caution`
- `over_budget_packet`
- `irrelevant_context_preserved`
- `unsafe_policy_simplification`
- `serialization_mismatch`
- `packet_validation_failure`

### V1 cap
Maximum active negative constraints per packet class: **12**.

---

## Schema Validation Rules

Every schema in the V1 bundle must support:

1. required-field validation
2. enum validation
3. type validation
4. missing-field rejection
5. forbidden-extra-field rejection where applicable
6. invalid fixture rejection
7. valid fixture acceptance

---

## Blocker Rule

The following condition blocks runtime code:

- any required schema missing
- any required enum unlocked
- any required fixture bundle missing
- any schema without at least one invalid fixture

---

## Required Next Artifact

After this document is accepted, BDS must produce the actual machine-readable schema bundle.

This document does not replace the schema bundle.
It governs it.

---

## Final Position

PACT V1 is packet-first.
If the packet and segment contracts are not real, V1 is not real.

