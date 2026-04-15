# BDS PACT V1 Evaluation Corpus Manifest

**Date:** 2026-04-10  
**Time:** America/New_York  
**Intended destination:** `98-drafts/BDS_PACT_V1_EVALUATION_CORPUS_MANIFEST.md`

---

## Purpose

This document defines the minimum starter evaluation corpus required for PACT V1.

It exists because earlier plans required an eval corpus but did not make the corpus structure concrete enough to begin replay and regression work.

---

## Core Rule

PACT V1 cannot proceed safely without a starter corpus that supports:
- packet correctness checks
- degradation-path checks
- replay checks
- permission-boundary checks
- pruning-fidelity checks
- serialization-profile checks

The corpus is a Phase 0 artifact, not a later improvement task.

---

## Minimum Corpus Size

The starter V1 corpus must contain at least **50 cases** spread across the required classes below.

This is a minimum floor, not an ideal target.

---

## Required Corpus Classes

### Class 1 — Golden success cases
Purpose:
- prove the happy path for each V1 packet class

Minimum count:
- 18

### Class 2 — Degraded-but-safe cases
Purpose:
- prove minimum viable packet or degraded safe operation

Minimum count:
- 8

### Class 3 — Safe-failure cases
Purpose:
- prove deterministic block and safe-failure packet behavior

Minimum count:
- 6

### Class 4 — Malformed or invalid input cases
Purpose:
- prove intake rejection, serialization rejection, or validation failure

Minimum count:
- 5

### Class 5 — Permission-boundary cases
Purpose:
- prove cache and packet isolation by permission context

Minimum count:
- 5

### Class 6 — Over-budget cases
Purpose:
- prove token-budget enforcement and degradation or safe-failure behavior

Minimum count:
- 4

### Class 7 — Grounding-failure cases
Purpose:
- prove packet classes that require grounding fail or degrade correctly when support cannot be attached

Minimum count:
- 2

### Class 8 — Adversarial retrieval or injection-carrier cases
Purpose:
- prove hostile or misleading retrieved content does not silently pass through as clean support

Minimum count:
- 2

---

## Required Per-Case Fields

Each corpus case must contain at minimum:

- `case_id`
- `case_class`
- `packet_class`
- `request_input`
- `consumer_identity`
- `permission_context`
- `source_set_ref`
- `expected_outcome_type`
- `expected_degradation_state`
- `expected_model_call_allowed`
- `expected_serialization_profile`
- `expected_lineage_scope`
- `expected_grounding_required`
- `notes`

---

## Recommended Corpus File Structure

```text
corpus/
  corpus_manifest.json
  cases/
    golden_success.jsonl
    degraded_safe.jsonl
    safe_failure.jsonl
    malformed_invalid.jsonl
    permission_boundary.jsonl
    over_budget.jsonl
    grounding_failure.jsonl
    adversarial_retrieval.jsonl
  sources/
    source_set_index.json
```

---

## Expected Outcome Types

Allowed V1 expected outcome types:
- `normal_packet`
- `degraded_packet`
- `minimum_viable_packet`
- `safe_failure_packet`
- `intake_rejection`

No case may use vague labels such as “probably good” or “should work.”

---

## Packet-Class Distribution Rule

The corpus must not overfit to only one packet class.

Minimum distribution:
- `answer_packet`: 20 cases
- `policy_response_packet`: 15 cases
- `search_assist_packet`: 15 cases

---

## Replay Requirement

For each corpus case, retained data must be sufficient to support:
- deterministic request replay
- packet hash comparison
- degradation-state comparison
- model-call-allowed comparison

Where model output quality is evaluated, the corpus must also support:
- grounded answer comparison
- support/ref comparison
- regression notes

---

## Quality Comparison Requirement

PACT V1 must be compared against a naive baseline.

For each applicable case, the corpus run should capture:
- naive prompt token estimate
- final PACT packet token count
- reduction percentage
- answer quality comparison result
- grounding sufficiency result

---

## Adversarial Case Rules

Adversarial cases should include at least:
- hostile retrieved content attempting instruction override
- misleading support content with plausible relevance but wrong authority class

These cases must not be treated as optional.

---

## Maintenance Rules

### Rule 1 — Corpus cases are versioned artifacts
They are not disposable test scraps.

### Rule 2 — Corpus changes require manifest updates
Adding or retiring cases must update `corpus_manifest.json`.

### Rule 3 — Failed production incidents may become corpus candidates
But only after review, redaction, and approval.

---

## Immediate Next Actions

1. create `corpus/` directory
2. create `corpus_manifest.json`
3. create the 8 required class files as JSONL placeholders
4. add first 10 high-confidence golden success cases
5. add first 5 degraded and safe-failure cases before runtime coding begins

---

## Final Position

PACT V1 cannot claim replayability or safe degradation without a corpus that makes those claims testable.

The corpus is part of the foundation, not future polish.

