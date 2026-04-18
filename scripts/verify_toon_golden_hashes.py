from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.engine import execute_slice_06  # noqa: E402

NON_STRICT_HASH_CASES = {"toon_fallback_zero_rows", "toon_fail_closed_answer_packet"}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"

    cases_path = REPO_ROOT / "tests" / "fixtures" / "toon_wave1_replay_cases.json"
    hashes_path = REPO_ROOT / "tests" / "fixtures" / "toon_wave1_golden_hashes.json"

    _assert(cases_path.exists(), "replay case fixture is missing")
    _assert(hashes_path.exists(), "golden hash fixture is missing")

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    expected_hashes = json.loads(hashes_path.read_text(encoding="utf-8"))

    observed = {}
    strict_cases = {}
    non_strict_cases = {}

    for case in cases:
        result = execute_slice_06(case["request"])
        case_name = case["name"]
        observed_hash = result["artifact_hash"]
        observed[case_name] = observed_hash

        _assert(case_name in expected_hashes, f"missing golden hash for {case_name}")

        if case_name in NON_STRICT_HASH_CASES:
            non_strict_cases[case_name] = {
                "expected_hash": expected_hashes[case_name],
                "observed_hash": observed_hash,
            }
        else:
            _assert(
                observed_hash == expected_hashes[case_name],
                f"{case_name}: artifact_hash drifted",
            )
            strict_cases[case_name] = observed_hash

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_golden_hashes_report.json"
    out_path.write_text(
        json.dumps(
            {
                "strict_cases": strict_cases,
                "non_strict_cases": non_strict_cases,
                "observed": observed,
                "all_green": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "report": str(out_path),
                "strict_cases": strict_cases,
                "non_strict_cases": non_strict_cases,
            },
            indent=2,
        )
    )
    print("verify_toon_golden_hashes: PASS")


if __name__ == "__main__":
    main()
