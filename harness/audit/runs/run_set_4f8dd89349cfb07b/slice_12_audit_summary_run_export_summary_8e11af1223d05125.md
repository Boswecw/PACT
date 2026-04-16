# PACT Run Export Summary Package

- export_package_id: `run_export_summary_8e11af1223d05125`
- run_id: `run_set_4f8dd89349cfb07b`
- transfer_id: `audit_transfer_f53923a4992f26db`
- receipt_count: `4`
- transfer_artifact_count: `14`
- package_artifact_count: `4`
- compatibility_posture: `compatible`
- source_run_index_path: `harness/audit/slice_11_run_export_index.json`
- source_transfer_manifest_path: `harness/audit/slice_10_audit_transfer_manifest_audit_transfer_f53923a4992f26db.json`
- source_transfer_bundle_path: `harness/audit/slice_10_audit_transfer_audit_transfer_f53923a4992f26db.zip`

## Packet Class Counts
- answer_packet: 1
- policy_response_packet: 2
- search_assist_packet: 1

## Result Kind Counts
- success: 3
- safe_failure: 1

## Execution Mode Counts
- live: 3
- replay: 1

## Degradation State Counts
- normal: 3
- retrieval_degraded: 0
- rerank_degraded: 0
- pruning_degraded: 0
- cache_degraded: 0
- minimum_viable_packet: 0
- safe_failure: 1

## Model Call Allowed Counts
- allowed: 3
- blocked: 1

## Compatibility Posture Counts
- compatible: 4
- migration_required: 0
- incompatible: 0

## Safe Failure Invocation
- safe_failure_invoked_count: 1

## Source Scopes
- request

## Included Package Paths
- transfer/run_audit_transfer_bundle.zip
- transfer/audit_transfer_manifest.json
- summary/audit_summary.md
- registry/export_registry_record.json

## Compatibility Note
- run_audit_transfer remains the nested governed bundle source for this package.
- manual receipt-list audit transfer remains available as a separate compatibility path.

## Receipt Detail
- receipt_id | packet_class | result_kind | execution_mode | compatibility_posture | degradation_state | model_call_allowed | safe_failure_invoked
- rcpt_0990c0414b9fec53 | search_assist_packet | success | live | compatible | normal | true | false
- rcpt_1ae7ddadb1e68689 | policy_response_packet | safe_failure | live | compatible | safe_failure | false | true
- rcpt_83c93bd52dc41068 | policy_response_packet | success | live | compatible | normal | true | false
- rcpt_c9d30156e36fd002 | answer_packet | success | replay | compatible | normal | true | false
