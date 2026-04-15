from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_06_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_06_verification_report.json"
TELEMETRY_DIR = ROOT / "harness" / "telemetry"
EVIDENCE_DIR = ROOT / "harness" / "evidence"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    return completed.returncode


def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1


def main() -> int:
    verify_slice_05 = ROOT / "scripts" / "verify_slice_05.py"
    if verify_slice_05.exists():
        if run([sys.executable, "scripts/verify_slice_05.py"]) != 0:
            return fail("Slice 05 verification did not pass under Slice 06.")

    for path in [TELEMETRY_DIR, EVIDENCE_DIR]:
        if path.exists():
            shutil.rmtree(path)

    sys.path.insert(0, str(ROOT))
    from runtime.engine import execute_slice_06  # noqa: WPS433

    cases = [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    counts = {"success": 0, "safe_failure": 0}
    results = []
    telemetry_paths = set()
    evidence_paths = set()

    for case in cases:
        if case["input"].get("prewarm_cache"):
            warm_input = dict(case["input"])
            warm_input.pop("prewarm_cache", None)
            warm_input["emit_telemetry"] = False
            warm_result = execute_slice_06(warm_input)
            if not warm_result["ok"]:
                return fail(f"{case['case_id']} cache prewarm failed")

        result = execute_slice_06(case["input"])
        packet = result["packet"]
        receipt = result["receipt"]
        expect = case["expect"]
        kind = "success" if result["ok"] else "safe_failure"

        if kind != expect["kind"]:
            return fail(f"{case['case_id']} kind mismatch")
        if packet["packet_class"] != expect["packet_class"]:
            return fail(f"{case['case_id']} packet_class mismatch")

        telemetry_path = Path(result["telemetry_path"])
        evidence_path = Path(result["evidence_path"])
        manifest_path = Path(result["manifest_path"])
        if not telemetry_path.exists():
            return fail(f"{case['case_id']} telemetry artifact missing")
        if not evidence_path.exists():
            return fail(f"{case['case_id']} evidence artifact missing")
        if not manifest_path.exists():
            return fail(f"{case['case_id']} manifest missing")

        telemetry_payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
        evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

        if telemetry_payload["cache_status"] != expect["cache_status"]:
            return fail(f"{case['case_id']} cache_status mismatch")

        if evidence_payload["receipt_id"] != receipt["receipt_id"]:
            return fail(f"{case['case_id']} evidence receipt mismatch")

        telemetry_paths.add(str(telemetry_path))
        evidence_paths.add(str(evidence_path))

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
                "telemetry_path": str(telemetry_path),
                "evidence_path": str(evidence_path),
            }
        )

    manifest_file = TELEMETRY_DIR / "slice_06_manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if len(manifest.get("entries", [])) != len(cases):
        return fail("manifest entry count mismatch")
    if len(telemetry_paths) != len(cases):
        return fail("telemetry paths are not unique")
    if len(evidence_paths) != len(cases):
        return fail("evidence paths are not unique")

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "manifest_entries": len(manifest.get("entries", [])),
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 06 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
