from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "99-contracts" / "schemas"
FIXTURE_ROOT = ROOT / "99-contracts" / "fixtures"
REPORT_PATH = ROOT / "99-contracts" / "schema_validation_report.json"

SCHEMA_FILES = [
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

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def normalize_refs(node, base_uri: str):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str) and v.startswith("./"):
                out[k] = f"{base_uri}/{v[2:]}"
            else:
                out[k] = normalize_refs(v, base_uri)
        return out
    if isinstance(node, list):
        return [normalize_refs(x, base_uri) for x in node]
    return node

def load_normalized_schemas():
    normalized = {}
    for filename in SCHEMA_FILES:
        raw = load_json(SCHEMA_DIR / filename)
        schema_id = raw.get("$id")
        if not schema_id:
            raise RuntimeError(f"{filename} missing $id")
        base_uri = schema_id.rsplit("/", 1)[0]
        normalized[schema_id] = normalize_refs(raw, base_uri)
    return normalized

def make_registry(normalized: dict[str, dict]) -> Registry:
    registry = Registry()
    pairs = []
    for uri, schema in normalized.items():
        pairs.append((uri, Resource.from_contents(schema)))
    return registry.with_resources(pairs)

def validate_one(validator, fixture_path: Path):
    data = load_json(fixture_path)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return data, errors

def main() -> int:
    normalized = load_normalized_schemas()
    registry = make_registry(normalized)
    summary = {
        "schema_bundle_version": "1.0.0",
        "report_kind": "fixture_validation",
        "valid_passed": [],
        "invalid_rejected": [],
        "edge_passed": [],
        "failures": [],
    }

    for filename in SCHEMA_FILES:
        original = load_json(SCHEMA_DIR / filename)
        schema_id = original["$id"]
        schema = normalized[schema_id]
        validator = Draft202012Validator(schema, registry=registry)

        base = filename.replace(".schema.json", "")
        valid_path = FIXTURE_ROOT / "valid" / f"{base}.valid.json"
        invalid_path = FIXTURE_ROOT / "invalid" / f"{base}.invalid.json"
        edge_path = FIXTURE_ROOT / "edge" / f"{base}.edge.json"

        for expected_path in [valid_path, invalid_path, edge_path]:
            if not expected_path.exists():
                summary["failures"].append({"schema": filename, "path": str(expected_path), "reason": "missing_fixture"})
                continue

        if valid_path.exists():
            _, errors = validate_one(validator, valid_path)
            if errors:
                summary["failures"].append({
                    "schema": filename,
                    "path": str(valid_path.relative_to(ROOT)),
                    "reason": "valid_fixture_failed",
                    "messages": [e.message for e in errors],
                })
            else:
                summary["valid_passed"].append(str(valid_path.relative_to(ROOT)))

        if invalid_path.exists():
            _, errors = validate_one(validator, invalid_path)
            if errors:
                summary["invalid_rejected"].append(str(invalid_path.relative_to(ROOT)))
            else:
                summary["failures"].append({
                    "schema": filename,
                    "path": str(invalid_path.relative_to(ROOT)),
                    "reason": "invalid_fixture_unexpectedly_passed",
                })

        if edge_path.exists():
            _, errors = validate_one(validator, edge_path)
            if errors:
                summary["failures"].append({
                    "schema": filename,
                    "path": str(edge_path.relative_to(ROOT)),
                    "reason": "edge_fixture_failed",
                    "messages": [e.message for e in errors],
                })
            else:
                summary["edge_passed"].append(str(edge_path.relative_to(ROOT)))

    summary["counts"] = {
        "valid_passed": len(summary["valid_passed"]),
        "invalid_rejected": len(summary["invalid_rejected"]),
        "edge_passed": len(summary["edge_passed"]),
        "failures": len(summary["failures"]),
    }

    REPORT_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary["counts"], indent=2))
    if summary["failures"]:
        print("CONTRACT FIXTURE VALIDATION FAILED")
        return 1

    print("CONTRACT FIXTURE VALIDATION PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
