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


def _compile_answer_packet(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
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


def _compile_policy_response_packet(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
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


def _compile_search_assist_packet(base: dict[str, Any], compile_input: dict[str, Any]) -> dict[str, Any]:
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


def compile_packet(normalized: dict[str, Any]) -> dict[str, Any]:
    packet_class = normalized["packet_class"]
    base = build_packet_base(normalized)
    compile_input = normalized["compile_input"]

    if packet_class == "answer_packet":
        packet = _compile_answer_packet(base, compile_input)
    elif packet_class == "policy_response_packet":
        packet = _compile_policy_response_packet(base, compile_input)
    elif packet_class == "search_assist_packet":
        packet = _compile_search_assist_packet(base, compile_input)
    else:
        raise PacketCompileError("unsupported packet class", public_reason_code="validation_failed")

    return finalize_packet_hash(packet)
