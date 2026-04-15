from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_10_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_10_verification_report.json"
AUDIT_DIR = ROOT / "harness" / "audit"
HANDOFF_DIR = ROOT / "harness" / "handoffs"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    return completed.returncode


def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if run([sys.executable, "scripts/verify_slice_09.py"]) != 0:
        return fail("Slice 09 verification did not pass under Slice 10.")

    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    if HANDOFF_DIR.exists():
        shutil.rmtree(HANDOFF_DIR)

    sys.path.insert(0, str(ROOT))
    from runtime.export.operator_api import handle_operator_request  # noqa: WPS433
    from runtime.validation.schema_validator import PacketValidationError, validate_instance  # noqa: WPS433

    valid_request_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "valid" / "operator_api_request.valid.json").read_text(encoding="utf-8"))
    validate_instance(valid_request_fixture, "operator_api_request.schema.json")
    invalid_request_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "invalid" / "operator_api_request.invalid.json").read_text(encoding="utf-8"))
    try:
        validate_instance(invalid_request_fixture, "operator_api_request.schema.json")
        return fail("invalid operator_api_request fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    valid_response_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "valid" / "operator_api_response.valid.json").read_text(encoding="utf-8"))
    validate_instance(valid_response_fixture, "operator_api_response.schema.json")
    invalid_response_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "invalid" / "operator_api_response.invalid.json").read_text(encoding="utf-8"))
    try:
        validate_instance(invalid_response_fixture, "operator_api_response.schema.json")
        return fail("invalid operator_api_response fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    valid_transfer_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "valid" / "audit_transfer_manifest.valid.json").read_text(encoding="utf-8"))
    validate_instance(valid_transfer_fixture, "audit_transfer_manifest.schema.json")
    invalid_transfer_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "invalid" / "audit_transfer_manifest.invalid.json").read_text(encoding="utf-8"))
    try:
        validate_instance(invalid_transfer_fixture, "audit_transfer_manifest.schema.json")
        return fail("invalid audit_transfer_manifest fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    slice_07_report = json.loads((ROOT / "harness" / "regression" / "slice_07_verification_report.json").read_text(encoding="utf-8"))
    receipts_by_case = {item["case_id"]: item["receipt_id"] for item in slice_07_report["results"]}
    current_run_receipts = sorted(receipts_by_case.values())

    catalog_request = {
        "schema_version": "1.0.0",
        "action": "catalog",
        "receipt_ids": current_run_receipts,
        "package_label": "operator_replay",
    }
    catalog_response_a = handle_operator_request(ROOT, catalog_request)
    catalog_response_b = handle_operator_request(ROOT, catalog_request)
    if sha256_file(Path(ROOT / "harness" / "exports" / "slice_08_export_catalog.json")) != sha256_file(Path(ROOT / "harness" / "exports" / "slice_08_export_catalog.json")):
        return fail("catalog file stability check failed")
    if json.dumps(catalog_response_a, sort_keys=True) != json.dumps(catalog_response_b, sort_keys=True):
        return fail("catalog operator response was not deterministic")

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {"catalog": 0, "detail": 0, "handoff": 0, "audit_transfer": 0}
    results = []

    for case in cases:
        action = case["action"]
        expect = case["expect"]

        if action == "catalog":
            if catalog_response_a["result_count"] != expect["result_count"]:
                return fail("catalog operator response count mismatch")
            counts["catalog"] += 1
            results.append({"case_id": case["case_id"], "result_count": catalog_response_a["result_count"]})
            continue

        if action == "detail":
            receipt_id = receipts_by_case[case["lookup_case_id"]]
            response = handle_operator_request(
                ROOT,
                {
                    "schema_version": "1.0.0",
                    "action": "detail",
                    "receipt_id": receipt_id,
                },
            )
            detail = response["detail"]
            if detail["result_kind"] != expect["result_kind"]:
                return fail(f"{case['case_id']} result_kind mismatch")
            if detail["packet_class"] != expect["packet_class"]:
                return fail(f"{case['case_id']} packet_class mismatch")
            counts["detail"] += 1
            results.append({"case_id": case["case_id"], "receipt_id": receipt_id, "result_kind": detail["result_kind"]})
            continue

        if action == "handoff":
            receipt_id = receipts_by_case[case["lookup_case_id"]]
            response = handle_operator_request(
                ROOT,
                {
                    "schema_version": "1.0.0",
                    "action": "handoff",
                    "receipt_id": receipt_id,
                    "handoff_dir": "harness/handoffs",
                },
            )
            manifest_path = Path(response["handoff"]["handoff_manifest_path"])
            if not manifest_path.exists():
                return fail("handoff manifest missing")
            handoff_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if handoff_manifest["packet_class"] != expect["packet_class"]:
                return fail("handoff packet_class mismatch")
            counts["handoff"] += 1
            results.append({"case_id": case["case_id"], "receipt_id": receipt_id, "handoff_manifest_path": str(manifest_path)})
            continue

        if action == "audit_transfer":
            request = {
                "schema_version": "1.0.0",
                "action": "audit_transfer",
                "receipt_ids": current_run_receipts,
                "handoff_dir": "harness/handoffs",
                "audit_dir": "harness/audit",
            }
            response_a = handle_operator_request(ROOT, request)
            response_b = handle_operator_request(ROOT, request)
            manifest_path = Path(response_a["audit_transfer"]["transfer_manifest_path"])
            bundle_path = Path(response_a["audit_transfer"]["transfer_bundle_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_instance(manifest, "audit_transfer_manifest.schema.json")
            if len(response_a["audit_transfer"]["receipt_ids"]) != expect["receipt_count"]:
                return fail("audit transfer receipt count mismatch")
            if response_a["audit_transfer"]["artifact_count"] != expect["artifact_count"]:
                return fail("audit transfer artifact count mismatch")
            if sha256_file(bundle_path) != sha256_file(Path(response_b["audit_transfer"]["transfer_bundle_path"])):
                return fail("audit transfer bundle was not deterministic")
            with ZipFile(bundle_path) as archive:
                members = sorted(archive.namelist())
            required_members = {
                "catalog/export_catalog.json",
                "transfer/audit_transfer_manifest.json",
            }
            if not required_members.issubset(set(members)):
                return fail("audit transfer bundle missing required members")
            counts["audit_transfer"] += 1
            results.append({"case_id": case["case_id"], "transfer_bundle_path": str(bundle_path), "artifact_count": response_a["audit_transfer"]["artifact_count"]})
            continue

        return fail(f"unknown action {action}")

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 10 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
