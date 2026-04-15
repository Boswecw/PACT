from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.shared.pact_utils import (
    build_source_lineage_digest,
    canonical_json,
    ensure_string_list,
    now_utc_iso,
    sha256_hex,
    stable_id,
)

ALLOWED_PACKET_CLASSES = {
    "answer_packet",
    "policy_response_packet",
    "search_assist_packet",
}

ALLOWED_SERIALIZATION_PROFILES = {
    "plain_text_only",
    "plain_text_with_compact_fields",
    "plain_text_with_json_segment",
    "plain_text_with_toon_segment",
}

ALLOWED_RETRIEVAL_MODES = {"hybrid", "lexical_only", "vector_only", "cache_only"}
ALLOWED_PRUNING_MODES = {"standard", "reduced", "none"}


@dataclass
class IntakeNormalizationError(Exception):
    message: str
    public_reason_code: str
    failure_state: str = "intake_rejection"

    def __str__(self) -> str:
        return self.message


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise IntakeNormalizationError(
            "request must be an object",
            public_reason_code="validation_failed",
        )

    packet_class = request.get("packet_class")
    if packet_class not in ALLOWED_PACKET_CLASSES:
        raise IntakeNormalizationError(
            "packet_class is missing or invalid",
            public_reason_code="validation_failed",
        )

    consumer_identity = request.get("consumer_identity")
    if not isinstance(consumer_identity, str) or not consumer_identity.strip():
        raise IntakeNormalizationError(
            "consumer_identity is required",
            public_reason_code="validation_failed",
        )

    permission_context = request.get("permission_context")
    if not isinstance(permission_context, dict) or not permission_context:
        raise IntakeNormalizationError(
            "permission_context is required and must be a non-empty object",
            public_reason_code="permission_unresolved",
        )

    compile_input = request.get("compile_input")
    if not isinstance(compile_input, dict):
        raise IntakeNormalizationError(
            "compile_input is required and must be an object",
            public_reason_code="validation_failed",
        )

    serialization_profile = request.get("serialization_profile", "plain_text_only")
    if serialization_profile not in ALLOWED_SERIALIZATION_PROFILES:
        raise IntakeNormalizationError(
            "serialization_profile is invalid for V1",
            public_reason_code="serialization_failed",
        )

    retrieval_mode = request.get("retrieval_mode", "lexical_only")
    if retrieval_mode not in ALLOWED_RETRIEVAL_MODES:
        raise IntakeNormalizationError(
            "retrieval_mode is invalid",
            public_reason_code="validation_failed",
        )

    pruning_mode = request.get("pruning_mode", "none")
    if pruning_mode not in ALLOWED_PRUNING_MODES:
        raise IntakeNormalizationError(
            "pruning_mode is invalid",
            public_reason_code="validation_failed",
        )

    now = request.get("now") or now_utc_iso()
    seed = {
        "packet_class": packet_class,
        "consumer_identity": consumer_identity,
        "permission_context": permission_context,
        "compile_input": compile_input,
        "serialization_profile": serialization_profile,
    }

    request_id = request.get("request_id") or stable_id("req", seed)
    trace_id = request.get("trace_id") or stable_id("trace", seed)
    warnings = ensure_string_list(request.get("warnings", []))
    restrictions = ensure_string_list(request.get("restrictions", []))
    grounding_required = bool(request.get("grounding_required", True))
    ttl_seconds = int(request.get("ttl_seconds", 300))

    source_lineage_input = {
        "packet_class": packet_class,
        "source_set_ref": request.get("source_set_ref"),
        "compile_input": compile_input,
    }

    return {
        "schema_version": "1.0.0",
        "packet_class": packet_class,
        "consumer_identity": consumer_identity.strip(),
        "permission_context": permission_context,
        "permission_context_digest": sha256_hex(canonical_json(permission_context)),
        "compile_input": compile_input,
        "serialization_profile": serialization_profile,
        "retrieval_mode": retrieval_mode,
        "pruning_mode": pruning_mode,
        "request_id": request_id,
        "trace_id": trace_id,
        "now": now,
        "ttl_seconds": ttl_seconds,
        "grounding_required": grounding_required,
        "warnings": warnings,
        "restrictions": restrictions,
        "source_lineage_digest": build_source_lineage_digest(source_lineage_input, "request"),
        "version_set": {
            "contract_version": request.get("contract_version", "1.0.0"),
            "runtime_version": request.get("runtime_version", "slice_03"),
            "corpus_version": request.get("corpus_version", "starter"),
            "budget_version": request.get("budget_version", "v1_lock"),
            "compatibility_posture": "compatible",
        },
    }
