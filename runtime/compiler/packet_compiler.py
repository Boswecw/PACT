from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .packet_base_builder import build_packet_base, finalize_packet_hash


@dataclass
class PacketCompileError(Exception):
    message: str
    public_reason_code: str = "validation_failed"
    failure_state: str = "compiler_failure"

    def __str__(self) -> str:
        return self.message


def _merge_known_fields(base: dict[str, Any], compile_input: dict[str, Any], field_names: list[str]) -> dict[str, Any]:
    packet = dict(base)
    for field_name in field_names:
        if field_name in compile_input:
            packet[field_name] = compile_input[field_name]
    return packet


def _compile_answer_packet_legacy(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
    return _merge_known_fields(
        base,
        compile_input,
        [
            "task_goal",
            "instruction_block",
            "support_blocks",
            "grounding_refs",
            "answer_constraints",
        ],
    )


def _compile_policy_response_packet_legacy(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
    return _merge_known_fields(
        base,
        compile_input,
        [
            "policy_scope",
            "policy_statements",
            "required_cautions",
            "grounding_refs",
            "disallowed_answer_modes",
        ],
    )


def _compile_search_assist_packet_legacy(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
    packet = _merge_known_fields(
        base,
        compile_input,
        [
            "search_goal",
            "ranked_result_blocks",
            "selection_constraints",
            "grounding_refs",
            "result_count",
        ],
    )
    if "ranked_result_blocks" in packet and "result_count" not in packet:
        packet["result_count"] = len(packet["ranked_result_blocks"])
    return packet


def compile_packet_legacy(normalized: dict[str, Any]) -> dict[str, Any]:
    packet_class = normalized["packet_class"]
    base = build_packet_base(normalized)
    compile_input = normalized["compile_input"]

    if packet_class == "answer_packet":
        packet = _compile_answer_packet_legacy(base, compile_input)
    elif packet_class == "policy_response_packet":
        packet = _compile_policy_response_packet_legacy(base, compile_input)
    elif packet_class == "search_assist_packet":
        packet = _compile_search_assist_packet_legacy(base, compile_input)
    else:
        raise PacketCompileError("unsupported packet class", public_reason_code="validation_failed")

    return finalize_packet_hash(packet)


def _derive_answer_packet(base: dict[str, Any], compile_input: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    grounding_refs = compile_input.get("grounding_refs", [])
    support_blocks = compile_input.get("support_blocks", [])
    return {
        **base,
        "task_goal": compile_input.get("task_goal") or normalized.get("retrieval_goal") or "Answer the request using grounded material.",
        "instruction_block": compile_input.get("instruction_block") or "Use only the selected grounded material.",
        "support_blocks": support_blocks,
        "grounding_refs": grounding_refs,
        "answer_constraints": compile_input.get("answer_constraints", []),
    }


def _derive_policy_response_packet(base: dict[str, Any], compile_input: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    grounding_refs = compile_input.get("grounding_refs", [])
    policy_statements = compile_input.get("policy_statements", [])
    return {
        **base,
        "policy_scope": compile_input.get("policy_scope") or normalized.get("retrieval_goal") or "policy_response",
        "policy_statements": policy_statements,
        "required_cautions": compile_input.get("required_cautions", ["Return only grounded policy guidance."]),
        "grounding_refs": grounding_refs,
        "disallowed_answer_modes": compile_input.get("disallowed_answer_modes", []),
    }


def _derive_search_assist_packet(base: dict[str, Any], compile_input: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    result_blocks = compile_input.get("ranked_result_blocks", [])
    return {
        **base,
        "search_goal": compile_input.get("search_goal") or normalized.get("retrieval_goal") or "Return ranked grounded search assistance.",
        "ranked_result_blocks": result_blocks,
        "selection_constraints": compile_input.get("selection_constraints", []),
        "grounding_refs": compile_input.get("grounding_refs", []),
        "result_count": compile_input.get("result_count", len(result_blocks)),
    }


def compile_packet(normalized: dict[str, Any]) -> dict[str, Any]:
    packet_class = normalized["packet_class"]
    base = build_packet_base(normalized)
    compile_input = normalized["compile_input"]

    if packet_class == "answer_packet":
        packet = _derive_answer_packet(base, compile_input, normalized)
    elif packet_class == "policy_response_packet":
        packet = _derive_policy_response_packet(base, compile_input, normalized)
    elif packet_class == "search_assist_packet":
        packet = _derive_search_assist_packet(base, compile_input, normalized)
    else:
        raise PacketCompileError("unsupported packet class", public_reason_code="validation_failed")

    return finalize_packet_hash(packet)
