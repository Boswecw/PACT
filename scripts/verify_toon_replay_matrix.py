from __future__ import annotations

import os

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.engine import execute_slice_06  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"
    fixture_path = REPO_ROOT / "tests" / "fixtures" / "toon_wave1_replay_cases.json"
    _assert(fixture_path.exists(), "replay fixture file is missing")

    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    results = []

    for case in cases:
        result = execute_slice_06(case["request"])
        receipt = result["receipt"]
        evidence = receipt["serialization_evidence"]
        expected = case["expected"]

        _assert(result["ok"] == expected["ok"], f"{case['name']}: ok mismatch")
        _assert(result["packet"]["packet_class"] == expected["packet_class"], f"{case['name']}: packet_class mismatch")
        _assert(evidence["requested_profile"] == expected["requested_profile"], f"{case['name']}: requested_profile mismatch")
        _assert(evidence["used_profile"] == expected["used_profile"], f"{case['name']}: used_profile mismatch")
        _assert(evidence["artifact_kind"] == expected["artifact_kind"], f"{case['name']}: artifact_kind mismatch")
        _assert(evidence["fallback_used"] == expected["fallback_used"], f"{case['name']}: fallback_used mismatch")

        if "row_count" in expected:
            _assert(evidence["segment_meta"]["row_count"] == expected["row_count"], f"{case['name']}: row_count mismatch")
        if "fallback_reason" in expected:
            _assert(evidence["fallback_reason"] == expected["fallback_reason"], f"{case['name']}: fallback_reason mismatch")
        if "public_reason_code" in expected:
            _assert(result["packet"]["public_reason_code"] == expected["public_reason_code"], f"{case['name']}: public_reason_code mismatch")

        results.append(
            {
                "name": case["name"],
                "ok": result["ok"],
                "used_profile": evidence["used_profile"],
                "artifact_kind": evidence["artifact_kind"],
                "fallback_used": evidence["fallback_used"],
                "artifact_hash": result["artifact_hash"],
            }
        )

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_replay_matrix_report.json"
    out_path.write_text(json.dumps({"cases": results, "all_green": True}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"report": str(out_path), "cases": results}, indent=2))
    print("verify_toon_replay_matrix: PASS")


if __name__ == "__main__":
    main()
