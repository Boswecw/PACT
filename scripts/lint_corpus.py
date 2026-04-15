from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
REPORT_PATH = CORPUS_DIR / "corpus_lint_report.json"

REQUIRED_CASE_FILES = [
    "golden_success.jsonl",
    "degraded_safe.jsonl",
    "safe_failure.jsonl",
    "malformed_invalid.jsonl",
    "permission_boundary.jsonl",
    "over_budget.jsonl",
    "grounding_failure.jsonl",
    "serialization_mismatch.jsonl",
    "adversarial_retrieval.jsonl",
]

REQUIRED_FIELDS = {
    "case_id","case_class","packet_class","request_input","consumer_identity",
    "permission_context","source_set_ref","expected_outcome_type","expected_degradation_state",
    "expected_model_call_allowed","expected_serialization_profile","expected_lineage_scope",
    "expected_grounding_required","notes"
}

def fail(msg: str) -> int:
    print(f"CORPUS LINT FAIL: {msg}")
    return 1

def main() -> int:
    manifest = json.loads((CORPUS_DIR / "corpus_manifest.json").read_text(encoding="utf-8"))
    source_index = json.loads((CORPUS_DIR / "sources" / "source_set_index.json").read_text(encoding="utf-8"))
    allowed_source_refs = {x["source_set_ref"] for x in source_index["source_sets"]}

    counts = Counter()
    packet_counts = Counter()
    failures = []
    total = 0

    for filename in REQUIRED_CASE_FILES:
        path = CORPUS_DIR / "cases" / filename
        if not path.exists():
            failures.append(f"missing required case file: {filename}")
            continue
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            failures.append(f"case file is empty: {filename}")
            continue
        for idx, line in enumerate(lines, start=1):
            try:
                row = json.loads(line)
            except Exception as exc:
                failures.append(f"{filename} line {idx} invalid JSON: {exc}")
                continue
            missing = sorted(REQUIRED_FIELDS - set(row.keys()))
            if missing:
                failures.append(f"{filename} line {idx} missing fields: {missing}")
                continue
            if row["source_set_ref"] not in allowed_source_refs:
                failures.append(f"{filename} line {idx} unknown source_set_ref: {row['source_set_ref']}")
            counts[row["case_class"]] += 1
            packet_counts[row["packet_class"]] += 1
            total += 1

    if counts["golden_success"] < 10:
        failures.append(f"golden_success starter floor not met: {counts['golden_success']} < 10")
    if (counts["degraded_safe"] + counts["safe_failure"]) < 5:
        failures.append("combined degraded_safe + safe_failure starter floor not met")
    if counts["serialization_mismatch"] < 1:
        failures.append("serialization_mismatch starter coverage missing")

    if manifest.get("current_case_count") != total:
        failures.append(
            f"manifest current_case_count mismatch: {manifest.get('current_case_count')} != {total}"
        )

    report = {
        "report_kind": "corpus_lint",
        "manifest_version": manifest.get("schema_version"),
        "total_cases": total,
        "case_class_counts": dict(counts),
        "packet_class_counts": dict(packet_counts),
        "failures": failures,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "total_cases": total,
        "golden_success": counts["golden_success"],
        "degraded_safe": counts["degraded_safe"],
        "safe_failure": counts["safe_failure"],
        "serialization_mismatch": counts["serialization_mismatch"],
        "failures": len(failures),
    }, indent=2))

    if failures:
        print("CORPUS LINT FAILED")
        return 1

    print("CORPUS LINT PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
