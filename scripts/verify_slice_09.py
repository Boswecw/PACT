from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_09_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_09_verification_report.json"
HANDOFF_DIR = ROOT / "harness" / "handoffs"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    return completed.returncode


def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1


def stable_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def main() -> int:
    if run([sys.executable, "scripts/verify_slice_08.py"]) != 0:
        return fail("Slice 08 verification did not pass under Slice 09.")

    if HANDOFF_DIR.exists():
        shutil.rmtree(HANDOFF_DIR)

    sys.path.insert(0, str(ROOT))
    from runtime.export.control_plane_surface import query_export_surface  # noqa: WPS433
    from runtime.validation.schema_validator import PacketValidationError, validate_instance  # noqa: WPS433

    valid_response_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "valid" / "export_control_plane_response.valid.json").read_text(encoding="utf-8")
    )
    validate_instance(valid_response_fixture, "export_control_plane_response.schema.json")

    invalid_response_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "invalid" / "export_control_plane_response.invalid.json").read_text(encoding="utf-8")
    )
    try:
        validate_instance(invalid_response_fixture, "export_control_plane_response.schema.json")
        return fail("invalid control-plane response fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    valid_handoff_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "valid" / "export_handoff_manifest.valid.json").read_text(encoding="utf-8")
    )
    validate_instance(valid_handoff_fixture, "export_handoff_manifest.schema.json")

    invalid_handoff_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "invalid" / "export_handoff_manifest.invalid.json").read_text(encoding="utf-8")
    )
    try:
        validate_instance(invalid_handoff_fixture, "export_handoff_manifest.schema.json")
        return fail("invalid handoff manifest fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    slice_07_report = json.loads(
        (ROOT / "harness" / "regression" / "slice_07_verification_report.json").read_text(encoding="utf-8")
    )
    receipts_by_case = {item["case_id"]: item["receipt_id"] for item in slice_07_report["results"]}
    required_receipts = sorted(receipts_by_case.values())

    catalog_query = {
        "action": "catalog",
        "receipt_ids": required_receipts,
        "package_label": "operator_replay",
    }
    first_catalog = query_export_surface(ROOT, catalog_query)
    second_catalog = query_export_surface(ROOT, catalog_query)
    if stable_hash(first_catalog) != stable_hash(second_catalog):
        return fail("catalog control-plane query was not deterministic")

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {"catalog": 0, "detail": 0, "handoff": 0}
    results = []

    for case in cases:
        action = case["action"]
        expect = case["expect"]

        if action == "catalog":
            if first_catalog["result_count"] != expect["result_count"]:
                return fail("catalog query result_count mismatch")
            labels = {entry["package_label"] for entry in first_catalog["results"]}
            if labels != {expect["package_label"]}:
                return fail("catalog query package_label mismatch")
            counts["catalog"] += 1
            results.append({"case_id": case["case_id"], "result_count": first_catalog["result_count"]})
            continue

        receipt_id = receipts_by_case[case["lookup_case_id"]]
        if action == "detail":
            response = query_export_surface(ROOT, {"action": "detail", "receipt_id": receipt_id})
            detail = response["detail"]
            if detail["result_kind"] != expect["result_kind"]:
                return fail(f"{case['case_id']} result_kind mismatch")
            if detail["packet_class"] != expect["packet_class"]:
                return fail(f"{case['case_id']} packet_class mismatch")
            counts["detail"] += 1
            results.append({"case_id": case["case_id"], "receipt_id": receipt_id, "result_kind": detail["result_kind"]})
            continue

        if action == "handoff":
            response = query_export_surface(ROOT, {"action": "handoff", "receipt_id": receipt_id})
            handoff = response["handoff"]
            manifest_path = Path(handoff["handoff_manifest_path"])
            copied_zip = Path(handoff["copied_replay_package_path"])
            if not manifest_path.exists() or not copied_zip.exists():
                return fail("handoff artifacts missing")
            handoff_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_instance(handoff_manifest, "export_handoff_manifest.schema.json")
            source_zip = Path(handoff_manifest["source_replay_package_path"])
            if hashlib.sha256(source_zip.read_bytes()).hexdigest() != hashlib.sha256(copied_zip.read_bytes()).hexdigest():
                return fail("handoff replay package bytes changed")
            if handoff_manifest["packet_class"] != expect["packet_class"]:
                return fail("handoff packet_class mismatch")
            counts["handoff"] += 1
            results.append({"case_id": case["case_id"], "receipt_id": receipt_id, "handoff_manifest_path": str(manifest_path)})
            continue

        return fail(f"unknown action {action}")

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "catalog_query_result_count": first_catalog["result_count"],
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 09 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
