from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

required_dirs = [
    "99-contracts/schemas",
    "99-contracts/fixtures/valid",
    "99-contracts/fixtures/invalid",
    "99-contracts/fixtures/edge",
    "99-contracts/registry",
    "corpus/cases",
    "corpus/sources",
    "harness/replay",
    "harness/regression",
    "harness/adversarial",
    "runtime/intake",
    "runtime/retrieval",
    "runtime/pruning",
    "runtime/compiler",
    "runtime/validation",
    "runtime/cache",
    "runtime/receipts",
    "telemetry/contracts",
    "telemetry/retention",
    "telemetry/exporters",
    "control-plane/analysis",
    "control-plane/proposals",
    "control-plane/rollout",
    "adapters/app_adapters",
    "adapters/provider_adapters",
    "docs/plans",
    "docs/architecture",
    "docs/runbooks",
    "src/shared",
]

required_schemas = [
    "packet_base.schema.json",
    "answer_packet.schema.json",
    "policy_response_packet.schema.json",
    "search_assist_packet.schema.json",
    "safe_failure_packet.schema.json",
    "runtime_receipt.schema.json",
    "negative_constraint.schema.json",
    "serialization_profile_enum.schema.json",
    "degradation_state_enum.schema.json",
    "version_set.schema.json",
    "toon_segment.schema.json",
    "toon_segment_registry_v1.schema.json",
    "grounding_ref.schema.json",
    "source_lineage_digest.schema.json",
    "cache_manifest_entry.schema.json",
]

required_plan_docs = [
    "docs/plans/BDS_PACT_V1_MASTER_PLAN.md",
    "docs/plans/BDS_PACT_V1_SCHEMA_LOCK_PACK.md",
    "docs/plans/BDS_PACT_V1_REPO_SKELETON_AND_OWNERSHIP_MAP.md",
    "docs/plans/BDS_PACT_V1_EVALUATION_CORPUS_MANIFEST.md",
    "docs/plans/BDS_PACT_V1_VERIFICATION_GOVERNANCE_AND_READINESS_PLAN.md",
    "docs/architecture/BDS_PACT_V1_PACKET_AND_SERIALIZATION_CONTRACT_LOCK.md",
    "docs/architecture/BDS_PACT_V1_RUNTIME_ARCHITECTURE_AND_DEGRADATION_SPEC.md",
    "docs/architecture/BDS_PACT_V1_QUANTITATIVE_BUDGET_LOCK.md",
    "docs/architecture/BDS_PACT_V1_THREAT_MODEL_APPENDIX.md",
    "docs/runbooks/COPY_PASTE_DEVELOPMENT_PROTOCOL_zip_slice_edition_2026-04-15.md",
]

packet_base_required = {
    "schema_version","packet_id","packet_class","packet_revision","request_id","trace_id",
    "consumer_identity","permission_context_digest","source_lineage_digest","serialization_profile",
    "lifecycle_state","freshness_state","admissibility_state","created_at","expires_at","packet_hash",
    "grounding_required","warnings","restrictions"
}

expected_serialization_profiles = {
    "plain_text_only",
    "plain_text_with_compact_fields",
    "plain_text_with_json_segment",
    "plain_text_with_toon_segment",
}

expected_degradation_states = {
    "normal",
    "retrieval_degraded",
    "rerank_degraded",
    "pruning_degraded",
    "cache_degraded",
    "minimum_viable_packet",
    "safe_failure",
}

required_case_fields = {
    "case_id","case_class","packet_class","request_input","consumer_identity",
    "permission_context","source_set_ref","expected_outcome_type","expected_degradation_state",
    "expected_model_call_allowed","expected_serialization_profile","expected_lineage_scope",
    "expected_grounding_required","notes"
}

def fail(msg: str) -> None:
    print(f"VERIFY FAIL: {msg}")
    sys.exit(1)

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path} did not parse as JSON: {exc}")

for rel in required_dirs:
    p = ROOT / rel
    if not p.exists() or not p.is_dir():
        fail(f"required directory missing: {rel}")

for rel in required_plan_docs:
    p = ROOT / rel
    if not p.exists():
        fail(f"required plan or protocol doc missing: {rel}")

schema_dir = ROOT / "99-contracts/schemas"
schema_docs = {}
for filename in required_schemas:
    path = schema_dir / filename
    if not path.exists():
        fail(f"required schema missing: {filename}")
    schema_docs[filename] = load_json(path)

packet_base = schema_docs["packet_base.schema.json"]
packet_base_required_found = set(packet_base.get("required", []))
missing_packet_base_required = sorted(packet_base_required - packet_base_required_found)
if missing_packet_base_required:
    fail(f"packet_base.schema.json missing required fields: {missing_packet_base_required}")

serialization_enum = schema_docs["serialization_profile_enum.schema.json"]
if set(serialization_enum.get("enum", [])) != expected_serialization_profiles:
    fail("serialization_profile_enum.schema.json does not match the locked V1 enum")

degradation_enum = schema_docs["degradation_state_enum.schema.json"]
if set(degradation_enum.get("enum", [])) != expected_degradation_states:
    fail("degradation_state_enum.schema.json does not match the locked V1 enum")

fixture_basenames = [name.replace(".schema.json", "") for name in required_schemas]
for base_name in fixture_basenames:
    valid = ROOT / f"99-contracts/fixtures/valid/{base_name}.valid.json"
    invalid = ROOT / f"99-contracts/fixtures/invalid/{base_name}.invalid.json"
    edge = ROOT / f"99-contracts/fixtures/edge/{base_name}.edge.json"
    if not valid.exists():
        fail(f"missing valid fixture: {valid}")
    if not invalid.exists():
        fail(f"missing invalid fixture: {invalid}")
    if not edge.exists():
        fail(f"missing edge fixture: {edge}")
    load_json(valid)
    load_json(invalid)
    load_json(edge)

registry_path = ROOT / "99-contracts/registry/toon_segment_registry_v1.json"
registry = load_json(registry_path)
if "row_definitions" not in registry:
    fail("TOON registry data exists but row_definitions is missing")

manifest = load_json(ROOT / "corpus/corpus_manifest.json")
case_files = manifest.get("case_files")
if not isinstance(case_files, list) or not case_files:
    fail("corpus_manifest.json case_files must be a non-empty list")

current_case_count = 0
for rel in case_files:
    path = ROOT / "corpus" / rel
    if not path.exists():
        fail(f"missing corpus case file from manifest: {rel}")
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        fail(f"corpus case file is empty: {rel}")
    for idx, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except Exception as exc:
            fail(f"{rel} line {idx} did not parse as JSON: {exc}")
        missing = sorted(required_case_fields - set(row.keys()))
        if missing:
            fail(f"{rel} line {idx} missing required fields: {missing}")
        current_case_count += 1

if manifest.get("current_case_count") != current_case_count:
    fail(
        "corpus_manifest.json current_case_count does not match actual JSONL row count "
        f"({manifest.get('current_case_count')} != {current_case_count})"
    )

print("Verified required directories.")
print("Verified required schemas and locked enums.")
print("Verified valid/invalid/edge fixtures for each schema.")
print(f"Verified corpus seed files and counted {current_case_count} starter cases.")
print("Verified plan and protocol docs under docs/.")
print("SLICE 01 VERIFICATION PASSED")
