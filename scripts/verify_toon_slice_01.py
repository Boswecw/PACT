from __future__ import annotations

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


def _print_pass(label: str, payload: dict) -> None:
    receipt = payload["receipt"]
    evidence = receipt["serialization_evidence"]
    print(
        json.dumps(
            {
                "case": label,
                "ok": payload["ok"],
                "packet_class": payload["packet"]["packet_class"],
                "requested_profile": evidence["requested_profile"],
                "used_profile": evidence["used_profile"],
                "artifact_kind": evidence["artifact_kind"],
                "fallback_used": evidence["fallback_used"],
                "receipt_schema_version": receipt["schema_version"],
            },
            indent=2,
        )
    )


def case_toon_success() -> None:
    request = {
        "packet_class": "search_assist_packet",
        "consumer_identity": "slice01_verify",
        "permission_context": {"mode": "standard"},
        "serialization_profile": "plain_text_with_toon_segment",
        "emit_telemetry": False,
        "compile_input": {
            "search_goal": "Find deterministic rendering examples.",
            "selection_constraints": ["Prefer policy-safe examples."],
            "ranked_result_blocks": [
                {
                    "rank": 1,
                    "title": "Alpha result",
                    "source_ref": "doc://alpha",
                    "summary": "Alpha summary with | delimiter and\nnew line.",
                },
                {
                    "rank": 2,
                    "title": "Beta result",
                    "source_ref": "doc://beta",
                    "summary": "Beta summary",
                },
            ],
            "grounding_refs": [
                {
                    "grounding_id": "g1",
                    "source_ref": "doc://alpha",
                    "authority_class": "primary",
                    "excerpt": "Alpha excerpt",
                    "start_offset": 0,
                    "end_offset": 12,
                }
            ],
            "result_count": 2,
        },
    }
    result = execute_slice_06(request)
    evidence = result["receipt"]["serialization_evidence"]
    _assert(result["ok"] is True, "TOON success case should succeed")
    _assert(result["receipt"]["schema_version"] == "1.1.0", "receipt schema should upgrade to 1.1.0")
    _assert(evidence["used_profile"] == "plain_text_with_toon_segment", "TOON profile should be used")
    _assert(evidence["artifact_kind"] == "toon_segment", "artifact_kind should be toon_segment")
    _assert(evidence["fallback_used"] is False, "fallback should not be used")
    _assert(evidence["segment_meta"]["row_count"] == 2, "row_count should be 2")
    _assert(result["artifact_text"].startswith("[TOON_SEGMENT|segment_version=1.0.0|row_definition_id=ranked_result_row_v1|row_count=2]"), "header mismatch")
    _assert("\\|" in result["artifact_text"], "delimiter should be escaped in TOON output")
    _print_pass("toon_success", result)


def case_toon_fallback_zero_rows() -> None:
    request = {
        "packet_class": "search_assist_packet",
        "consumer_identity": "slice01_verify",
        "permission_context": {"mode": "standard"},
        "serialization_profile": "plain_text_with_toon_segment",
        "emit_telemetry": False,
        "compile_input": {
            "search_goal": "Find nothing",
            "selection_constraints": [],
            "ranked_result_blocks": [],
            "grounding_refs": [],
            "result_count": 0,
        },
    }
    result = execute_slice_06(request)
    evidence = result["receipt"]["serialization_evidence"]
    _assert(result["ok"] is True, "fallback case should stay successful")
    _assert(evidence["fallback_used"] is True, "fallback should be used")
    _assert(evidence["fallback_reason"] == "no_renderable_rows", "fallback reason mismatch")
    _assert(evidence["used_profile"] == "plain_text_only", "fallback should downgrade to plain_text_only")
    _assert(evidence["artifact_kind"] == "plain_text", "fallback artifact_kind should be plain_text")
    _assert(evidence["segment_meta"] is None, "fallback should not include segment_meta")
    _print_pass("toon_fallback_zero_rows", result)


def case_toon_fail_closed_answer_packet() -> None:
    request = {
        "packet_class": "answer_packet",
        "consumer_identity": "slice01_verify",
        "permission_context": {"mode": "standard"},
        "serialization_profile": "plain_text_with_toon_segment",
        "emit_telemetry": False,
        "compile_input": {
            "task_goal": "Answer the question",
            "instruction_block": "Use the evidence.",
            "support_blocks": ["Support block"],
            "grounding_refs": [
                {
                    "grounding_id": "g1",
                    "source_ref": "doc://policy",
                    "authority_class": "primary",
                    "excerpt": "Policy excerpt",
                    "start_offset": 0,
                    "end_offset": 12,
                }
            ],
            "answer_constraints": ["Do not invent facts."],
        },
    }
    result = execute_slice_06(request)
    receipt = result["receipt"]
    evidence = receipt["serialization_evidence"]
    _assert(result["ok"] is False, "answer_packet TOON case should fail closed")
    _assert(receipt["safe_failure_invoked"] is True, "safe failure should be invoked")
    _assert(receipt["model_call_allowed"] is False, "model call should be blocked")
    _assert(evidence["requested_profile"] == "plain_text_with_toon_segment", "requested profile mismatch")
    _assert(result["packet"]["public_reason_code"] == "serialization_failed", "public_reason_code mismatch")
    _print_pass("toon_fail_closed_answer_packet", result)


def main() -> None:
    case_toon_success()
    case_toon_fallback_zero_rows()
    case_toon_fail_closed_answer_packet()
    print("slice_01_pact_toon_serialization_boundary: PASS")


if __name__ == "__main__":
    main()
