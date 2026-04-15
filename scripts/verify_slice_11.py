from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_11_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_11_verification_report.json"
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
    if run([sys.executable, "scripts/verify_slice_10.py"]) != 0:
        return fail("Slice 10 verification did not pass under Slice 11.")

    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    if HANDOFF_DIR.exists():
        shutil.rmtree(HANDOFF_DIR)

    sys.path.insert(0, str(ROOT))
    from runtime.export.operator_api import handle_operator_request  # noqa: WPS433
    from runtime.export.run_index import build_run_export_index  # noqa: WPS433
    from runtime.validation.schema_validator import PacketValidationError, validate_instance  # noqa: WPS433

    for name, schema in [
        ("run_export_index.valid.json", "run_export_index.schema.json"),
        ("operator_api_request.valid.json", "operator_api_request.schema.json"),
        ("operator_api_response.valid.json", "operator_api_response.schema.json"),
        ("audit_transfer_manifest.valid.json", "audit_transfer_manifest.schema.json"),
    ]:
        payload = json.loads((ROOT / "99-contracts" / "fixtures" / "valid" / name).read_text(encoding="utf-8"))
        validate_instance(payload, schema)

    for name, schema in [
        ("run_export_index.invalid.json", "run_export_index.schema.json"),
        ("operator_api_request.invalid.json", "operator_api_request.schema.json"),
        ("operator_api_response.invalid.json", "operator_api_response.schema.json"),
        ("audit_transfer_manifest.invalid.json", "audit_transfer_manifest.schema.json"),
    ]:
        payload = json.loads((ROOT / "99-contracts" / "fixtures" / "invalid" / name).read_text(encoding="utf-8"))
        try:
            validate_instance(payload, schema)
            return fail(f"invalid fixture unexpectedly passed validation: {name}")
        except PacketValidationError:
            pass

    slice_07_report = json.loads((ROOT / "harness" / "regression" / "slice_07_verification_report.json").read_text(encoding="utf-8"))
    current_run_receipts = sorted({item["receipt_id"] for item in slice_07_report["results"]})

    run_index_a = build_run_export_index(ROOT)
    run_index_b = build_run_export_index(ROOT)
    if sha256_file(Path(run_index_a["index_path"])) != sha256_file(Path(run_index_b["index_path"])):
        return fail("run export index build was not deterministic")

    run_id = run_index_a["index"]["runs"][0]["run_id"]

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {"run_index": 0, "operator_run_index": 0, "run_audit_transfer": 0, "manual_audit_transfer": 0}
    results = []

    for case in cases:
        action = case["action"]
        expect = case["expect"]

        if action == "run_index":
            index = run_index_a["index"]
            validate_instance(index, "run_export_index.schema.json")
            if index["run_count"] != expect["run_count"]:
                return fail("run export index run_count mismatch")
            if index["runs"][0]["receipt_count"] != expect["receipt_count"]:
                return fail("run export index receipt_count mismatch")
            counts["run_index"] += 1
            results.append({"case_id": case["case_id"], "run_id": run_id, "receipt_count": index["runs"][0]["receipt_count"]})
            continue

        if action == "operator_run_index":
            response = handle_operator_request(
                ROOT,
                {"schema_version": "1.0.0", "action": "run_index", "audit_dir": "harness/audit"},
            )
            if response["run_index"]["run_count"] != expect["run_count"]:
                return fail("operator run_index response mismatch")
            counts["operator_run_index"] += 1
            results.append({"case_id": case["case_id"], "run_count": response["run_index"]["run_count"]})
            continue

        if action == "run_audit_transfer":
            request = {
                "schema_version": "1.0.0",
                "action": "run_audit_transfer",
                "run_id": run_id,
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
                return fail("run audit transfer receipt count mismatch")
            if response_a["audit_transfer"]["artifact_count"] != expect["artifact_count"]:
                return fail("run audit transfer artifact count mismatch")
            if sha256_file(bundle_path) != sha256_file(Path(response_b["audit_transfer"]["transfer_bundle_path"])):
                return fail("run audit transfer bundle was not deterministic")
            with ZipFile(bundle_path) as archive:
                members = set(archive.namelist())
            required_members = {
                "catalog/export_catalog.json",
                "run_index/run_export_index.json",
                "transfer/audit_transfer_manifest.json",
            }
            if not required_members.issubset(members):
                return fail("run audit transfer bundle missing required members")
            counts["run_audit_transfer"] += 1
            results.append({"case_id": case["case_id"], "run_id": run_id, "artifact_count": response_a["audit_transfer"]["artifact_count"]})
            continue

        if action == "manual_audit_transfer":
            request = {
                "schema_version": "1.0.0",
                "action": "audit_transfer",
                "receipt_ids": current_run_receipts,
                "handoff_dir": "harness/handoffs",
                "audit_dir": "harness/audit",
            }
            response = handle_operator_request(ROOT, request)
            if len(response["audit_transfer"]["receipt_ids"]) != expect["receipt_count"]:
                return fail("manual audit transfer receipt count mismatch")
            if response["audit_transfer"]["artifact_count"] != expect["artifact_count"]:
                return fail("manual audit transfer artifact count mismatch")
            counts["manual_audit_transfer"] += 1
            results.append({"case_id": case["case_id"], "artifact_count": response["audit_transfer"]["artifact_count"]})
            continue

        return fail(f"unknown action {action}")

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 11 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
