from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_07_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_07_verification_report.json"
EXPORT_DIR = ROOT / "harness" / "exports"
EXPORT_DIR_REPEAT = ROOT / "harness" / "exports_repeat"
TELEMETRY_DIR = ROOT / "harness" / "telemetry"
EVIDENCE_DIR = ROOT / "harness" / "evidence"


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
    verify_slice_06 = ROOT / "scripts" / "verify_slice_06.py"
    if verify_slice_06.exists():
        if run([sys.executable, "scripts/verify_slice_06.py"]) != 0:
            return fail("Slice 06 verification did not pass under Slice 07.")

    for path in [EXPORT_DIR, EXPORT_DIR_REPEAT, TELEMETRY_DIR, EVIDENCE_DIR]:
        if path.exists():
            shutil.rmtree(path)

    sys.path.insert(0, str(ROOT))
    from runtime.engine import execute_slice_07  # noqa: WPS433
    from runtime.export.bundle_builder import build_export_bundle  # noqa: WPS433
    from runtime.validation.schema_validator import PacketValidationError, validate_instance  # noqa: WPS433

    valid_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "valid" / "export_bundle_manifest.valid.json").read_text(encoding="utf-8"))
    validate_instance(valid_fixture, "export_bundle_manifest.schema.json")
    invalid_fixture = json.loads((ROOT / "99-contracts" / "fixtures" / "invalid" / "export_bundle_manifest.invalid.json").read_text(encoding="utf-8"))
    try:
        validate_instance(invalid_fixture, "export_bundle_manifest.schema.json")
        return fail("invalid export manifest fixture unexpectedly passed validation")
    except PacketValidationError:
        pass

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {"success": 0, "safe_failure": 0}
    results = []
    deterministic_bundle_matches = 0

    for case in cases:
        if case["input"].get("prewarm_cache"):
            warm_input = dict(case["input"])
            warm_input.pop("prewarm_cache", None)
            warm_input["emit_telemetry"] = False
            warm_input["emit_control_plane_export"] = False
            warm_result = execute_slice_07(warm_input)
            if not warm_result["ok"]:
                return fail(f"{case['case_id']} cache prewarm failed")

        result = execute_slice_07(case["input"])
        packet = result["packet"]
        receipt = result["receipt"]
        expect = case["expect"]
        kind = "success" if result["ok"] else "safe_failure"

        if kind != expect["kind"]:
            return fail(f"{case['case_id']} kind mismatch")
        if packet["packet_class"] != expect["packet_class"]:
            return fail(f"{case['case_id']} packet_class mismatch")
        if not result.get("control_plane_export_ok"):
            return fail(f"{case['case_id']} control-plane export flag missing")

        telemetry_path = Path(result["telemetry_path"])
        evidence_path = Path(result["evidence_path"])
        runtime_manifest_path = Path(result["manifest_path"])
        export_manifest_path = Path(result["export_manifest_path"])
        replay_package_path = Path(result["replay_package_path"])

        for label, path in [
            ("telemetry", telemetry_path),
            ("evidence", evidence_path),
            ("runtime manifest", runtime_manifest_path),
            ("export manifest", export_manifest_path),
            ("replay package", replay_package_path),
        ]:
            if not path.exists():
                return fail(f"{case['case_id']} {label} missing")

        telemetry_payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
        export_manifest = json.loads(export_manifest_path.read_text(encoding="utf-8"))
        validate_instance(export_manifest, "export_bundle_manifest.schema.json")

        if telemetry_payload["cache_status"] != expect["cache_status"]:
            return fail(f"{case['case_id']} cache_status mismatch")
        if export_manifest["package_label"] != expect["package_label"]:
            return fail(f"{case['case_id']} package_label mismatch")
        if export_manifest["result_kind"] != kind:
            return fail(f"{case['case_id']} result_kind mismatch")
        if export_manifest["receipt_id"] != receipt["receipt_id"]:
            return fail(f"{case['case_id']} export receipt mismatch")

        with zipfile.ZipFile(replay_package_path) as archive:
            names = archive.namelist()
            required = {
                "manifest/export_bundle_manifest.json",
                "replay/request.json",
                "observed/packet.json",
                "observed/receipt.json",
            }
            if not required.issubset(set(names)):
                return fail(f"{case['case_id']} replay package missing required members")
            archived_manifest = json.loads(archive.read("manifest/export_bundle_manifest.json"))
            if archived_manifest != export_manifest:
                return fail(f"{case['case_id']} archived manifest mismatch")

        repeat = build_export_bundle(
            ROOT,
            request=case["input"],
            result=result,
            export_dir="harness/exports_repeat",
            package_label=expect["package_label"],
        )
        repeat_package_path = Path(repeat["replay_package_path"])
        if sha256_file(replay_package_path) != sha256_file(repeat_package_path):
            return fail(f"{case['case_id']} replay package determinism mismatch")
        deterministic_bundle_matches += 1

        if kind == "success":
            counts["success"] += 1
        else:
            if packet["failure_state"] != expect["failure_state"]:
                return fail(f"{case['case_id']} failure_state mismatch")
            if packet["public_reason_code"] != expect["public_reason_code"]:
                return fail(f"{case['case_id']} public_reason_code mismatch")
            counts["safe_failure"] += 1

        results.append(
            {
                "case_id": case["case_id"],
                "kind": kind,
                "packet_class": packet["packet_class"],
                "receipt_id": receipt["receipt_id"],
                "export_manifest_path": str(export_manifest_path),
                "replay_package_path": str(replay_package_path),
            }
        )

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "deterministic_bundle_matches": deterministic_bundle_matches,
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 07 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
