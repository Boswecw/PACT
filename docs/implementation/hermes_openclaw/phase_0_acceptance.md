# Hermes + OpenClaw Phase 0 Acceptance

**Status:** accepted  
**Operator:** Charlie  
**Date:** 2026-04-17  
**Phase:** 0 — Decision Lock

## Acceptance summary
This record accepts the authority model, the first proving slice, and the repo split for the Hermes + OpenClaw protocol-driven implementation plan.

## Decision markers
decision_lock_status: accepted  
proving_slice_status: accepted  
repo_split_status: accepted  

proving_slice: documentation-drift-digest

## Accepted authority model
- no_master_orchestrator_above_yellowjacket: true
- yellowjacket_sole_runtime_admission_point: true
- openclaw_requests_are_intents_only: true
- openclaw_direct_to_hermes_bypass_forbidden: true
- hermes_executes_yellowjacket_issued_packets_only: true
- hermes_returns_receipts_and_results_only: true
- hermes_does_not_own_schedule_truth: true
- hermes_does_not_own_replay_admission: true
- hermes_does_not_own_approvals: true
- hermes_direct_app_writeback_forbidden: true
- memory_v1_disabled: true
- subagents_v1_forbidden: true

## Accepted repo split
- yellowjacket_contract_authority_surface: accepted
- yellowjacket_runtime_owner: accepted
- yellowjacket_add_package: yellowjacket-execution-adapters
- hermes_repo_mode: standalone_execution_provider_runtime
- openclaw_repo_mode: standalone_operator_control_plane
- openclaw_code_inside_yellowjacket_core: forbidden
- hermes_execution_logic_inside_yellowjacket_core: forbidden
- yellowjacket_openclaw_core_package: forbidden

## Accepted first proving slice
The first Hermes/OpenClaw proving slice is:

`documentation-drift-digest`

Why this slice is accepted first:
- low business risk
- useful operator value
- easy to baseline
- easy to replay
- exercises schedule, replay, degraded-state, and review-packet pathways without touching canonical content

## Gate statement
No Phase 1 package skeleton work begins until this Phase 0 acceptance record is present and the Phase 0 gate passes.
