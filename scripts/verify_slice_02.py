from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    return completed.returncode

def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1

def main() -> int:
    if not (ROOT / "scripts" / "verify_slice_01.py").exists():
        return fail("Slice 01 foundation is missing. Apply Slice 01 first.")

    if run([sys.executable, "scripts/verify_slice_01.py"]) != 0:
        return fail("Slice 01 verification did not pass under Slice 02.")

    if run([sys.executable, "scripts/validate_contract_fixtures.py"]) != 0:
        return fail("Contract fixture validation failed.")

    if run([sys.executable, "scripts/lint_corpus.py"]) != 0:
        return fail("Corpus lint failed.")

    report_path = ROOT / "99-contracts" / "schema_validation_report.json"
    if not report_path.exists():
        return fail("schema_validation_report.json was not produced")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    counts = report.get("counts", {})
    if counts.get("failures", 1) != 0:
        return fail("schema_validation_report.json contains failures")
    if counts.get("valid_passed") != 15:
        return fail("schema validation did not pass all 15 valid fixtures")
    if counts.get("invalid_rejected") != 15:
        return fail("schema validation did not reject all 15 invalid fixtures")
    if counts.get("edge_passed") != 15:
        return fail("schema validation did not pass all 15 edge fixtures")

    corpus_report_path = ROOT / "corpus" / "corpus_lint_report.json"
    if not corpus_report_path.exists():
        return fail("corpus_lint_report.json was not produced")
    corpus_report = json.loads(corpus_report_path.read_text(encoding="utf-8"))
    if corpus_report.get("failures"):
        return fail("corpus_lint_report.json contains failures")
    if corpus_report.get("case_class_counts", {}).get("golden_success", 0) < 10:
        return fail("golden_success floor not met")
    if (
        corpus_report.get("case_class_counts", {}).get("degraded_safe", 0)
        + corpus_report.get("case_class_counts", {}).get("safe_failure", 0)
    ) < 5:
        return fail("degraded/safe_failure floor not met")
    if corpus_report.get("case_class_counts", {}).get("serialization_mismatch", 0) < 1:
        return fail("serialization_mismatch coverage missing")

    print("SLICE 02 VERIFICATION PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
