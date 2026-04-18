from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.engine import execute_slice_06  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _canonical_projection(result: dict) -> dict:
    receipt = result["receipt"]
    evidence = receipt["serialization_evidence"]
    projection = {
        "ok": result["ok"],
        "packet_class": result["packet"]["packet_class"],
        "requested_profile": evidence["requested_profile"],
        "used_profile": evidence["used_profile"],
        "artifact_kind": evidence["artifact_kind"],
        "fallback_used": evidence["fallback_used"],
    }
    if "fallback_reason" in evidence and evidence["fallback_reason"] is not None:
        projection["fallback_reason"] = evidence["fallback_reason"]
    if "public_reason_code" in result["packet"]:
        projection["public_reason_code"] = result["packet"]["public_reason_code"]
    return projection


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def main() -> None:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"

    cases_path = REPO_ROOT / "tests" / "fixtures" / "toon_wave1_replay_cases.json"
    targets_path = REPO_ROOT / "tests" / "fixtures" / "toon_wave1_non_strict_canonical_targets.json"

    _assert(cases_path.exists(), "replay case fixture is missing")
    _assert(targets_path.exists(), "non-strict canonical target fixture is missing")

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    targets = json.loads(targets_path.read_text(encoding="utf-8"))

    by_name = {case["name"]: case for case in cases}
    observed = {}

    for case_name, target in targets.items():
        _assert(case_name in by_name, f"missing replay case for {case_name}")
        result = execute_slice_06(by_name[case_name]["request"])
        projection = _canonical_projection(result)

        for key, expected_value in target.items():
            _assert(
                projection.get(key) == expected_value,
                f"{case_name}: canonical field mismatch for {key}",
            )

        observed[case_name] = {
            "projection": projection,
            "canonical_digest": _digest(projection),
        }

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_non_strict_canonical_report.json"
    out_path.write_text(
        json.dumps(
            {
                "targets": targets,
                "observed": observed,
                "all_green": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"report": str(out_path), "observed": observed}, indent=2))
    print("verify_toon_non_strict_canonical: PASS")


if __name__ == "__main__":
    main()
