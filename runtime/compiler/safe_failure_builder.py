from __future__ import annotations

from typing import Any

from src.shared.pact_utils import canonical_json, sha256_hex, stable_id


VALID_PACKET_CLASSES = {
    "answer_packet",
    "policy_response_packet",
    "search_assist_packet",
}


def _pick_packet_class(source: dict[str, Any] | None) -> str:
    if isinstance(source, dict):
        packet_class = source.get("packet_class")
        if packet_class in VALID_PACKET_CLASSES:
            return packet_class
    return "answer_packet"


def _pick_request_id(source: dict[str, Any] | None, packet_class: str) -> str:
    if isinstance(source, dict) and isinstance(source.get("request_id"), str):
        return source["request_id"]
    return stable_id("req", {"packet_class": packet_class, "source": source or {}})


def _pick_trace_id(source: dict[str, Any] | None, packet_class: str) -> str:
    if isinstance(source, dict) and isinstance(source.get("trace_id"), str):
        return source["trace_id"]
    return stable_id("trace", {"packet_class": packet_class, "source": source or {}})


def build_safe_failure_packet(
    source: dict[str, Any] | None,
    *,
    failure_state: str,
    public_reason_code: str,
    retry_allowed: bool = False,
) -> dict[str, Any]:
    packet_class = _pick_packet_class(source)
    request_id = _pick_request_id(source, packet_class)
    trace_id = _pick_trace_id(source, packet_class)
    seed = {
        "packet_class": packet_class,
        "request_id": request_id,
        "trace_id": trace_id,
        "failure_state": failure_state,
        "public_reason_code": public_reason_code,
    }
    failure_packet_id = stable_id("fpkt", seed)
    operator_trace_ref = f"optrace_{trace_id[-12:]}"
    packet = {
        "schema_version": "1.0.0",
        "failure_packet_id": failure_packet_id,
        "request_id": request_id,
        "trace_id": trace_id,
        "packet_class": packet_class,
        "failure_state": failure_state,
        "retry_allowed": retry_allowed,
        "operator_trace_ref": operator_trace_ref,
        "public_reason_code": public_reason_code,
    }
    packet["_derived_hash"] = sha256_hex(canonical_json(packet))
    return packet
