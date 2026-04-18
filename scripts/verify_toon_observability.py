from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.engine import execute_slice_06  # noqa: E402
from runtime.observability.toon_evidence import evidence_file_path, summarize_events  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _search_request() -> dict:
    return {
        "packet_class": "search_assist_packet",
        "consumer_identity": "wave1_observability_verify",
        "permission_context": {"mode": "standard"},
        "serialization_profile": "plain_text_with_toon_segment",
        "emit_telemetry": False,
        "compile_input": {
            "search_goal": "Observe TOON telemetry.",
            "selection_constraints": ["Prefer deterministic examples."],
            "ranked_result_blocks": [
                {
                    "rank": 1,
                    "title": "Alpha result",
                    "source_ref": "doc://alpha",
                    "summary": "Alpha summary",
                }
            ],
            "grounding_refs": [
                {
                    "grounding_id": "g1",
                    "source_ref": "doc://alpha",
                    "authority_class": "primary",
                    "excerpt": "Alpha excerpt",
                    "start_offset": 0,
                    "end_offset": 10,
                }
            ],
            "result_count": 1,
        },
    }


def _zero_rows_request() -> dict:
    request = _search_request()
    request["compile_input"]["ranked_result_blocks"] = []
    request["compile_input"]["result_count"] = 0
    return request


def _answer_request() -> dict:
    return {
        "packet_class": "answer_packet",
        "consumer_identity": "wave1_observability_verify",
        "permission_context": {"mode": "standard"},
        "serialization_profile": "plain_text_with_toon_segment",
        "emit_telemetry": False,
        "compile_input": {
            "task_goal": "Answer directly.",
            "instruction_block": "Stay within policy.",
            "support_blocks": ["Policy support"],
            "grounding_refs": [
                {
                    "grounding_id": "g1",
                    "source_ref": "doc://policy",
                    "authority_class": "primary",
                    "excerpt": "Policy excerpt",
                    "start_offset": 0,
                    "end_offset": 10,
                }
            ],
            "answer_constraints": ["No invention."],
        },
    }


def main() -> None:
    evidence_path = evidence_file_path()
    if evidence_path.exists():
        evidence_path.unlink()

    os.environ["PACT_ENABLE_TOON_WAVE1"] = "false"
    disabled = execute_slice_06(_search_request())
    _assert(disabled["receipt"]["serialization_evidence"]["fallback_reason"] == "toon_disabled", "flag-disabled case mismatch")

    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"
    success = execute_slice_06(_search_request())
    _assert(success["receipt"]["serialization_evidence"]["used_profile"] == "plain_text_with_toon_segment", "success case mismatch")

    fallback = execute_slice_06(_zero_rows_request())
    _assert(fallback["receipt"]["serialization_evidence"]["fallback_reason"] == "no_renderable_rows", "zero-row fallback mismatch")

    fail_closed = execute_slice_06(_answer_request())
    _assert(fail_closed["ok"] is False, "answer_packet TOON should fail closed")
    _assert(fail_closed["model_artifact_emitted"] is False, "fail-closed result should record model_artifact_emitted=false")

    summary = summarize_events()
    _assert(summary["total_events"] == 4, "expected four observability events")
    _assert(summary["toon_requested_count"] == 4, "expected four TOON requests")
    _assert(summary["toon_used_count"] == 1, "expected one actual TOON use")
    _assert(summary["fallback_count"] == 2, "expected two fallback cases")
    _assert(summary["fallback_reason_counts"].get("toon_disabled") == 1, "expected one toon_disabled event")
    _assert(summary["fallback_reason_counts"].get("no_renderable_rows") == 1, "expected one no_renderable_rows event")
    _assert(summary["packet_class_counts"].get("search_assist_packet") == 3, "expected three search_assist_packet events")
    _assert(summary["packet_class_counts"].get("answer_packet") == 1, "expected one answer_packet event")

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_observability_report.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"evidence_file": str(evidence_path), "report": str(out_path), "summary": summary}, indent=2))
    print("verify_toon_observability: PASS")


if __name__ == "__main__":
    main()
