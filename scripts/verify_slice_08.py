from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_08_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_08_verification_report.json"
DOWNLOAD_DIR = ROOT / "harness" / "downloads"


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
    if run([sys.executable, "scripts/verify_slice_07.py"]) != 0:
        return fail("Slice 07 verification did not pass under Slice 08.")

    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)

    sys.path.insert(0, str(ROOT))
    from runtime.export.operator_surface import build_export_catalog, get_export_bundle_detail, materialize_replay_package  # noqa: WPS433
    from runtime.validation.schema_validator import PacketValidationError, validate_instance  # noqa: WPS433

    valid_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "valid" / "export_catalog_manifest.valid.json").read_text(encoding="utf-8")
    )
    validate_instance(valid_fixture, "export_catalog_manifest.schema.json")

    invalid_fixture = json.loads(
        (ROOT / "99-contracts" / "fixtures" / "invalid" / "export_catalog_manifest.invalid.json").read_text(encoding="utf-8")
    )
    try:
        validate_instance(invalid_fixture, "export_catalog_manifest.schema.json")
        return fail("invalid export catalog fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    slice_07_report = json.loads(
        (ROOT / "harness" / "regression" / "slice_07_verification_report.json").read_text(encoding="utf-8")
    )
    receipts_by_case = {item["case_id"]: item["receipt_id"] for item in slice_07_report["results"]}
    required_receipts = set(receipts_by_case.values())

    first_catalog = build_export_catalog(ROOT, export_dir="harness/exports")
    second_catalog = build_export_catalog(ROOT, export_dir="harness/exports")
    first_catalog_path = Path(first_catalog["catalog_path"])
    second_catalog_path = Path(second_catalog["catalog_path"])
    if sha256_file(first_catalog_path) != sha256_file(second_catalog_path):
        return fail("export catalog rebuild was not deterministic")

    catalog = first_catalog["catalog"]
    validate_instance(catalog, "export_catalog_manifest.schema.json")

    catalog_by_receipt = {entry["receipt_id"]: entry for entry in catalog["entries"]}
    missing_receipts = sorted(required_receipts - set(catalog_by_receipt))
    if missing_receipts:
        return fail(f"catalog missing required receipts: {missing_receipts}")

    current_run_entries = [catalog_by_receipt[receipt_id] for receipt_id in sorted(required_receipts)]

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    counts = {"catalog": 0, "detail": 0, "download": 0}

    for case in cases:
        action = case["action"]
        expect = case["expect"]

        if action == "catalog":
            if len(current_run_entries) != expect["bundle_count"]:
                return fail("catalog current-run bundle_count mismatch")
            labels = {entry["package_label"] for entry in current_run_entries}
            if labels != {expect["package_label"]}:
                return fail("catalog current-run package_label set mismatch")
            counts["catalog"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "bundle_count": len(current_run_entries),
                    "catalog_total_entries": catalog["bundle_count"],
                }
            )
            continue

        receipt_id = receipts_by_case[case["lookup_case_id"]]
        if action == "detail":
            detail = get_export_bundle_detail(ROOT, receipt_id, export_dir="harness/exports")
            manifest = detail["manifest"]
            if manifest["result_kind"] != expect["kind"]:
                return fail(f"{case['case_id']} result_kind mismatch")
            if manifest["packet_class"] != expect["packet_class"]:
                return fail(f"{case['case_id']} packet_class mismatch")
            counts["detail"] += 1
            results.append({"case_id": case["case_id"], "receipt_id": receipt_id, "result_kind": manifest["result_kind"]})
            continue

        if action == "download":
            materialized = materialize_replay_package(
                ROOT,
                receipt_id,
                DOWNLOAD_DIR,
                export_dir="harness/exports",
                extract=True,
            )
            source_zip = Path(materialized["source_replay_package_path"])
            copied_zip = Path(materialized["copied_replay_package_path"])
            if sha256_file(source_zip) != sha256_file(copied_zip):
                return fail("downloaded replay package bytes changed")
            members = set(materialized["extracted_members"])
            if not set(expect["required_members"]).issubset(members):
                return fail("downloaded replay package missing required members")
            counts["download"] += 1
            results.append(
                {
                    "case_id": case["case_id"],
                    "receipt_id": receipt_id,
                    "copied_replay_package_path": str(copied_zip),
                }
            )
            continue

        return fail(f"unknown action {action}")

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "catalog_total_entries": catalog["bundle_count"],
        "current_run_bundle_count": len(current_run_entries),
        "catalog_path": first_catalog["catalog_path"],
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 08 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
