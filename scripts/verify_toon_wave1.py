from __future__ import annotations

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


def _base_search_request() -> dict:
    return {
        "packet_class": "search_assist_packet",
        "consumer_identity": "wave1_verify",
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
                    "summary": "Alpha summary with | delimiter and\nnew line plus [TOON_SEGMENT] token and ROW| token.",
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


def _answer_request() -> dict:
    return {
        "packet_class": "answer_packet",
        "consumer_identity": "wave1_verify",
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


def case_flag_disabled_fallback() -> dict:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "false"
    result = execute_slice_06(_base_search_request())
    evidence = result["receipt"]["serialization_evidence"]
    _assert(result["ok"] is True, "flag-disabled case should still succeed")
    _assert(evidence["used_profile"] == "plain_text_only", "flag-disabled case should fall back to plain_text_only")
    _assert(evidence["fallback_used"] is True, "flag-disabled case should record fallback")
    _assert(evidence["fallback_reason"] == "toon_disabled", "flag-disabled fallback reason mismatch")
    return result


def case_toon_replay_determinism() -> dict:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"
    first = execute_slice_06(_base_search_request())
    second = execute_slice_06(_base_search_request())
    first_ev = first["receipt"]["serialization_evidence"]
    second_ev = second["receipt"]["serialization_evidence"]

    _assert(first["ok"] is True and second["ok"] is True, "replay cases must succeed")
    _assert(first["artifact_text"] == second["artifact_text"], "artifact text must be stable across replay")
    _assert(first["artifact_hash"] == second["artifact_hash"], "artifact hash must be stable across replay")
    _assert(first_ev["segment_meta"]["segment_hash"] == second_ev["segment_meta"]["segment_hash"], "segment hash must be stable across replay")
    _assert(first_ev["token_estimates"] == second_ev["token_estimates"], "token deltas must be stable across replay")
    return first


def case_security_escaping() -> dict:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"
    result = execute_slice_06(_base_search_request())
    text = result["artifact_text"]
    _assert("\\|" in text, "pipe delimiter must be escaped")
    _assert("\\n" in text, "newlines must be normalized and escaped")
    _assert("\\[TOON_SEGMENT" in text, "reserved header token must be escaped")
    _assert("ROW\\|" in text, "reserved row token must be escaped")
    return result


def case_fail_closed_answer_packet() -> dict:
    os.environ["PACT_ENABLE_TOON_WAVE1"] = "true"
    result = execute_slice_06(_answer_request())
    _assert(result["ok"] is False, "answer_packet TOON should fail closed")
    _assert(result["receipt"]["safe_failure_invoked"] is True, "safe failure must be invoked")
    _assert(result["model_artifact_emitted"] is False, "model artifact should not be emitted for fail-closed result")
    return result


def emit_operator_evidence(success: dict, fallback: dict, fail_closed: dict) -> Path:
    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_wave1_operator_examples.md"

    success_ev = success["receipt"]["serialization_evidence"]
    fallback_ev = fallback["receipt"]["serialization_evidence"]
    fail_ev = fail_closed["receipt"]["serialization_evidence"]

    out_path.write_text(
        "\n".join(
            [
                "# TOON Wave 1 Operator Evidence",
                "",
                "## Example 1 — TOON success",
                f"- requested profile: {success_ev['requested_profile']}",
                f"- used profile: {success_ev['used_profile']}",
                f"- artifact kind: {success_ev['artifact_kind']}",
                f"- segment meta: {json.dumps(success_ev['segment_meta'], indent=2)}",
                f"- token estimates: {json.dumps(success_ev['token_estimates'], indent=2)}",
                "",
                "## Example 2 — Plain-text fallback",
                f"- requested profile: {fallback_ev['requested_profile']}",
                f"- used profile: {fallback_ev['used_profile']}",
                f"- fallback reason: {fallback_ev['fallback_reason']}",
                f"- segment meta: {fallback_ev['segment_meta']}",
                "",
                "## Example 3 — Fail-closed",
                f"- requested profile: {fail_ev['requested_profile']}",
                f"- render attempted: {fail_ev['render_attempted']}",
                f"- artifact emitted: {fail_closed['model_artifact_emitted']}",
                f"- fail-closed reason: {fail_closed['packet']['public_reason_code']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    disabled = case_flag_disabled_fallback()
    success = case_toon_replay_determinism()
    case_security_escaping()
    fail_closed = case_fail_closed_answer_packet()
    evidence_path = emit_operator_evidence(success, disabled, fail_closed)

    print(
        json.dumps(
            {
                "flag_disabled_used_profile": disabled["receipt"]["serialization_evidence"]["used_profile"],
                "replay_artifact_hash": success["artifact_hash"],
                "fail_closed_model_artifact_emitted": fail_closed["model_artifact_emitted"],
                "operator_evidence_path": str(evidence_path),
            },
            indent=2,
        )
    )
    print("verify_toon_wave1: PASS")


if __name__ == "__main__":
    main()
