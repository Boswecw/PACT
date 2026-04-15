from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "slice_04_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "slice_04_verification_report.json"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    return completed.returncode


def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1


def main() -> int:
    verify_slice_03 = ROOT / "scripts" / "verify_slice_03.py"
    if verify_slice_03.exists():
        if run([sys.executable, "scripts/verify_slice_03.py"]) != 0:
            return fail("Slice 03 verification did not pass under Slice 04.")

    sys.path.insert(0, str(ROOT))
    from runtime.engine import execute_slice_04  # noqa: WPS433

    if not CASE_FILE.exists():
        return fail("slice_04_cases.jsonl is missing")

    cases = []
    for idx, line in enumerate(CASE_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except Exception as exc:
            return fail(f"slice_04_cases.jsonl line {idx} did not parse: {exc}")

    counts = {
        "success": 0,
        "safe_failure": 0,
    }
    results = []

    for case in cases:
        result = execute_slice_04(case["input"])
        packet = result["packet"]
        receipt = result["receipt"]
        expect = case["expect"]

        kind = "success" if result["ok"] else "safe_failure"
        if kind != expect["kind"]:
            return fail(f"{case['case_id']} expected kind {expect['kind']} but got {kind}")

        if packet["packet_class"] != expect["packet_class"]:
            return fail(f"{case['case_id']} packet_class mismatch")

        if receipt["degradation_state"] != expect["degradation_state"]:
            return fail(f"{case['case_id']} degradation_state mismatch")

        if receipt["retrieval_mode"] != expect["retrieval_mode"]:
            return fail(f"{case['case_id']} retrieval_mode mismatch")

        if receipt["model_call_allowed"] != expect["model_call_allowed"]:
            return fail(f"{case['case_id']} model_call_allowed mismatch")

        if receipt["safe_failure_invoked"] != expect["safe_failure_invoked"]:
            return fail(f"{case['case_id']} safe_failure_invoked mismatch")

        if kind == "success":
            if packet.get("admissibility_state") != "admissible":
                return fail(f"{case['case_id']} success packet not admissible")
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
                "degradation_state": receipt["degradation_state"],
                "receipt_id": receipt["receipt_id"],
            }
        )

    report = {
        "total_cases": len(cases),
        "counts": counts,
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("SLICE 04 VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
