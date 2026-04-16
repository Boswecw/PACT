from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "harness" / "regression" / "slice_12_verification_report.json"
CASE_PATH = ROOT / "harness" / "regression" / "slice_12_cases.jsonl"
AUDIT_DIR = ROOT / "harness" / "audit"
HANDOFF_DIR = ROOT / "harness" / "handoffs"
EXPECTED_PACKAGE_MEMBERS = {
    "registry/export_registry_record.json",
    "summary/audit_summary.md",
    "summary/run_export_summary_package_manifest.json",
    "transfer/audit_transfer_manifest.json",
    "transfer/run_audit_transfer_bundle.zip",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        fail(f"command failed: {' '.join(command)}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def assert_count_sum(counts: dict[str, int], expected: int, label: str) -> None:
    actual = sum(counts.values())
    assert_true(actual == expected, f"{label} expected {expected}, got {actual}")


def main() -> None:
    run([sys.executable, "scripts/verify_slice_11.py"])

    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    if HANDOFF_DIR.exists():
        shutil.rmtree(HANDOFF_DIR)

    sys.path.insert(0, str(ROOT))

    from runtime.export.operator_api import handle_operator_request
    from runtime.export.run_export_summary_package import build_run_export_summary_package
    from runtime.export.run_index import build_run_export_index
    from runtime.validation.schema_validator import PacketValidationError, validate_instance

    try:
        validate_instance(
            load_json(ROOT / "99-contracts" / "fixtures" / "valid" / "run_export_summary_registry_record.valid.json"),
            "run_export_summary_registry_record.schema.json",
        )
        validate_instance(
            load_json(ROOT / "99-contracts" / "fixtures" / "valid" / "run_export_summary_package_manifest.valid.json"),
            "run_export_summary_package_manifest.schema.json",
        )
        try:
            validate_instance(
                load_json(ROOT / "99-contracts" / "fixtures" / "invalid" / "run_export_summary_registry_record.invalid.json"),
                "run_export_summary_registry_record.schema.json",
            )
            fail("invalid registry record fixture unexpectedly passed")
        except PacketValidationError:
            pass
        try:
            validate_instance(
                load_json(ROOT / "99-contracts" / "fixtures" / "invalid" / "run_export_summary_package_manifest.invalid.json"),
                "run_export_summary_package_manifest.schema.json",
            )
            fail("invalid summary manifest fixture unexpectedly passed")
        except PacketValidationError:
            pass
    except PacketValidationError as exc:
        fail(f"schema fixture validation failed: {exc}")

    run_index = build_run_export_index(ROOT)
    run_entry = run_index["index"]["runs"][0]
    run_id = run_entry["run_id"]
    receipt_ids = run_entry["receipt_ids"]

    cases = [json.loads(line) for line in CASE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {
        "run_export_summary_package": 0,
        "operator_run_export_summary_package": 0,
        "run_audit_transfer_compat": 0,
        "manual_audit_transfer_compat": 0,
    }
    results = []

    for case in cases:
        expect = case["expect"]

        if case["action"] == "summary_build":
            request = {
                "schema_version": "1.0.0",
                "action": "run_export_summary_package",
                "run_id": run_id,
                "handoff_dir": "harness/handoffs",
                "audit_dir": "harness/audit",
            }
            package_one = build_run_export_summary_package(ROOT, request)
            package_two = build_run_export_summary_package(ROOT, request)
            manifest = package_one["summary_manifest"]
            registry_record = package_one["registry_record"]
            manifest_path = Path(package_one["summary_manifest_path"])
            package_path = Path(package_one["summary_package_path"])
            summary_path = Path(package_one["summary_path"])
            registry_path = Path(package_one["registry_record_path"])

            assert_true(package_path.exists(), "summary package zip missing")
            assert_true(manifest_path.exists(), "summary package manifest missing")
            assert_true(summary_path.exists(), "summary markdown missing")
            assert_true(registry_path.exists(), "registry record missing")
            assert_true(registry_record["receipt_count"] == expect["receipt_count"], "registry receipt_count mismatch")
            assert_true(registry_record["transfer_artifact_count"] == expect["transfer_artifact_count"], "transfer artifact count mismatch")
            assert_true(registry_record["package_artifact_count"] == expect["package_artifact_count"], "package artifact count mismatch")
            assert_true(len(registry_record["receipt_ids"]) == expect["receipt_count"], "registry receipt id count mismatch")
            assert_true(manifest["artifact_count"] == expect["package_artifact_count"], "manifest artifact_count mismatch")
            assert_true(len(manifest["receipt_ids"]) == expect["receipt_count"], "manifest receipt_ids mismatch")
            assert_count_sum(registry_record["packet_class_counts"], expect["receipt_count"], "packet_class_counts")
            assert_count_sum(registry_record["result_kind_counts"], expect["receipt_count"], "result_kind_counts")
            assert_count_sum(registry_record["execution_mode_counts"], expect["receipt_count"], "execution_mode_counts")
            assert_count_sum(registry_record["degradation_state_counts"], expect["receipt_count"], "degradation_state_counts")
            assert_count_sum(registry_record["compatibility_posture_counts"], expect["receipt_count"], "compatibility_posture_counts")
            assert_count_sum(registry_record["model_call_allowed_counts"], expect["receipt_count"], "model_call_allowed_counts")
            assert_true(registry_record["safe_failure_invoked_count"] <= expect["receipt_count"], "safe_failure_invoked_count out of range")
            assert_true(sorted(registry_record["receipt_ids"]) == sorted(receipt_ids), "registry receipt ids do not match run index")

            summary_body = summary_path.read_text(encoding="utf-8")
            assert_true(f"run_id: `{run_id}`" in summary_body, "summary missing run_id line")
            assert_true(f"receipt_count: `{expect['receipt_count']}`" in summary_body, "summary missing receipt_count line")
            assert_true(f"transfer_artifact_count: `{expect['transfer_artifact_count']}`" in summary_body, "summary missing transfer_artifact_count line")

            package_hash_one = sha256_file(package_path)
            package_hash_two = sha256_file(Path(package_two["summary_package_path"]))
            assert_true(package_hash_one == package_hash_two, "summary package zip is not deterministic")

            with ZipFile(package_path) as archive:
                members = set(archive.namelist())
            assert_true(EXPECTED_PACKAGE_MEMBERS.issubset(members), "summary package zip missing expected members")
            assert_true(
                set(registry_record["included_paths"]) == EXPECTED_PACKAGE_MEMBERS - {"summary/run_export_summary_package_manifest.json"},
                "registry included_paths mismatch",
            )

            counts["run_export_summary_package"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "export_package_id": manifest["export_package_id"],
                    "summary_package_path": str(package_path),
                    "receipt_count": registry_record["receipt_count"],
                    "transfer_artifact_count": registry_record["transfer_artifact_count"],
                    "package_artifact_count": registry_record["package_artifact_count"],
                }
            )
            continue

        if case["action"] == "operator_run_export_summary_package":
            response = handle_operator_request(
                ROOT,
                {
                    "schema_version": "1.0.0",
                    "action": "run_export_summary_package",
                    "run_id": run_id,
                    "handoff_dir": "harness/handoffs",
                    "audit_dir": "harness/audit",
                },
            )
            validate_instance(response, "operator_api_response.schema.json")
            summary = response["run_export_summary_package"]
            manifest = load_json(Path(summary["summary_manifest_path"]))
            assert_true(summary["receipt_count"] == expect["receipt_count"], "operator summary receipt_count mismatch")
            assert_true(summary["artifact_count"] == expect["package_artifact_count"], "operator summary artifact_count mismatch")
            assert_true(len(summary["receipt_ids"]) == expect["receipt_count"], "operator summary receipt_ids mismatch")
            assert_true(manifest["artifact_count"] == expect["package_artifact_count"], "operator manifest artifact_count mismatch")
            counts["operator_run_export_summary_package"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "export_package_id": summary["export_package_id"],
                    "summary_package_path": summary["summary_package_path"],
                    "receipt_count": summary["receipt_count"],
                    "artifact_count": summary["artifact_count"],
                }
            )
            continue

        if case["action"] == "compat_run_audit_transfer":
            response = handle_operator_request(
                ROOT,
                {
                    "schema_version": "1.0.0",
                    "action": "run_audit_transfer",
                    "run_id": run_id,
                    "handoff_dir": "harness/handoffs",
                    "audit_dir": "harness/audit",
                },
            )
            validate_instance(response, "operator_api_response.schema.json")
            transfer = response["audit_transfer"]
            assert_true(len(transfer["receipt_ids"]) == expect["receipt_count"], "run_audit_transfer receipt count mismatch")
            assert_true(transfer["artifact_count"] == expect["artifact_count"], "run_audit_transfer artifact_count mismatch")
            counts["run_audit_transfer_compat"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "transfer_id": transfer["transfer_id"],
                    "artifact_count": transfer["artifact_count"],
                    "receipt_count": len(transfer["receipt_ids"]),
                }
            )
            continue

        if case["action"] == "compat_manual_audit_transfer":
            response = handle_operator_request(
                ROOT,
                {
                    "schema_version": "1.0.0",
                    "action": "audit_transfer",
                    "receipt_ids": receipt_ids,
                    "handoff_dir": "harness/handoffs",
                    "audit_dir": "harness/audit",
                },
            )
            validate_instance(response, "operator_api_response.schema.json")
            transfer = response["audit_transfer"]
            assert_true(len(transfer["receipt_ids"]) == expect["receipt_count"], "manual audit_transfer receipt count mismatch")
            assert_true(transfer["artifact_count"] == expect["artifact_count"], "manual audit_transfer artifact_count mismatch")
            counts["manual_audit_transfer_compat"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "transfer_id": transfer["transfer_id"],
                    "artifact_count": transfer["artifact_count"],
                    "receipt_count": len(transfer["receipt_ids"]),
                }
            )
            continue

        fail(f"unknown case action: {case['action']}")

    report = {
        "slice": 12,
        "total_cases": len(cases),
        "run_export_summary_package": counts["run_export_summary_package"],
        "operator_run_export_summary_package": counts["operator_run_export_summary_package"],
        "run_audit_transfer_compat": counts["run_audit_transfer_compat"],
        "manual_audit_transfer_compat": counts["manual_audit_transfer_compat"],
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Slice 12 verification passed")
    print(f"total_cases: {report['total_cases']}")
    print(f"run_export_summary_package: {report['run_export_summary_package']}")
    print(f"operator_run_export_summary_package: {report['operator_run_export_summary_package']}")
    print(f"run_audit_transfer_compat: {report['run_audit_transfer_compat']}")
    print(f"manual_audit_transfer_compat: {report['manual_audit_transfer_compat']}")


if __name__ == "__main__":
    main()
