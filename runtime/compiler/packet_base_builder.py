from __future__ import annotations

from typing import Any

from src.shared.pact_utils import add_seconds_to_timestamp, canonical_json, sha256_hex, stable_id


def build_packet_base(normalized: dict[str, Any]) -> dict[str, Any]:
    packet_seed = {
        "request_id": normalized["request_id"],
        "trace_id": normalized["trace_id"],
        "packet_class": normalized["packet_class"],
        "compile_input": normalized["compile_input"],
        "task_intent_id": normalized.get("task_intent_id"),
        "context_bundle_id": normalized.get("context_bundle_id"),
        "context_bundle_hash": normalized.get("context_bundle_hash"),
    }
    packet = {
        "schema_version": normalized["schema_version"],
        "packet_id": stable_id("pkt", packet_seed),
        "packet_class": normalized["packet_class"],
        "packet_revision": 1,
        "request_id": normalized["request_id"],
        "trace_id": normalized["trace_id"],
        "consumer_identity": normalized["consumer_identity"],
        "permission_context_digest": normalized["permission_context_digest"],
        "source_lineage_digest": normalized["source_lineage_digest"],
        "serialization_profile": normalized["serialization_profile"],
        "lifecycle_state": "compiled",
        "freshness_state": "fresh",
        "admissibility_state": "pending",
        "created_at": normalized["now"],
        "expires_at": add_seconds_to_timestamp(normalized["now"], normalized["ttl_seconds"]),
        "packet_hash": "",
        "grounding_required": normalized["grounding_required"],
        "warnings": list(normalized["warnings"]),
        "restrictions": list(normalized["restrictions"]),
    }
    if normalized.get("task_intent_id"):
        packet["task_intent_id"] = normalized["task_intent_id"]
    if normalized.get("context_bundle_id"):
        packet["context_bundle_id"] = normalized["context_bundle_id"]
    if normalized.get("context_bundle_hash"):
        packet["context_bundle_hash"] = normalized["context_bundle_hash"]
    return packet


def finalize_packet_hash(packet: dict[str, Any]) -> dict[str, Any]:
    packet_copy = dict(packet)
    packet_copy["packet_hash"] = ""
    packet["packet_hash"] = sha256_hex(canonical_json(packet_copy))
    return packet
