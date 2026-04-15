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
ALLOWED_EXECUTION_MODES = {"replay", "live"}


@dataclass
class IntakeNormalizationError(Exception):
    message: str
    public_reason_code: str
    failure_state: str = "intake_rejection"

    def __str__(self) -> str:
        return self.message


def _normalize_retrieval_input(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise IntakeNormalizationError(
            "retrieval_input must be a list",
            public_reason_code="validation_failed",
        )
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise IntakeNormalizationError(
                f"retrieval_input[{idx}] must be an object",
                public_reason_code="validation_failed",
            )
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise IntakeNormalizationError(
                f"retrieval_input[{idx}].source_ref is required",
                public_reason_code="validation_failed",
            )
        content = item.get("content", item.get("excerpt", ""))
        if not isinstance(content, str):
            raise IntakeNormalizationError(
                f"retrieval_input[{idx}].content must be a string when provided",
                public_reason_code="validation_failed",
            )
        normalized.append(
            {
                "source_ref": source_ref.strip(),
                "title": item.get("title") or source_ref.strip(),
                "content": content,
                "authority_class": item.get("authority_class", "secondary"),
                "lexical_score": float(item.get("lexical_score", 1.0)),
                "vector_score": float(item.get("vector_score", 0.0)),
            }
        )
    return normalized


def _normalize_adapter_config(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IntakeNormalizationError(
            "adapter_config must be an object",
            public_reason_code="validation_failed",
        )
    return value


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

    execution_mode = request.get("execution_mode", "replay")
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        raise IntakeNormalizationError(
            "execution_mode is invalid",
            public_reason_code="validation_failed",
        )

    compile_input = request.get("compile_input", {})
    if not isinstance(compile_input, dict):
        raise IntakeNormalizationError(
            "compile_input must be an object",
            public_reason_code="validation_failed",
        )

    retrieval_input = _normalize_retrieval_input(request.get("retrieval_input"))
    adapter_config = _normalize_adapter_config(request.get("adapter_config"))
    live_query = request.get("live_query") or request.get("retrieval_goal") or ""

    has_live_inputs = bool(adapter_config.get("live_corpus")) or bool(adapter_config.get("provider_id")) or bool(adapter_config.get("provider_ref")) or bool(live_query)
    if not compile_input and not retrieval_input and not (execution_mode == "live" and has_live_inputs):
        raise IntakeNormalizationError(
            "compile_input, retrieval_input, or live adapter input is required",
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
        "retrieval_input": retrieval_input,
        "serialization_profile": serialization_profile,
        "execution_mode": execution_mode,
        "live_query": live_query,
        "cache_key": request.get("cache_key"),
        "adapter_config": adapter_config,
    }

    request_id = request.get("request_id") or stable_id("req", seed)
    trace_id = request.get("trace_id") or stable_id("trace", {"seed": seed, "now": now})
    warnings = ensure_string_list(request.get("warnings", []))
    restrictions = ensure_string_list(request.get("restrictions", []))
    grounding_required = bool(request.get("grounding_required", True))
    ttl_seconds = int(request.get("ttl_seconds", 300))

    source_lineage_input = {
        "packet_class": packet_class,
        "source_set_ref": request.get("source_set_ref"),
        "compile_input": compile_input,
        "retrieval_input": retrieval_input,
        "execution_mode": execution_mode,
        "adapter_config": adapter_config,
        "live_query": live_query,
        "cache_key": request.get("cache_key"),
    }

    allow_minimum_viable_packet = bool(
        request.get(
            "allow_minimum_viable_packet",
            packet_class in {"answer_packet", "search_assist_packet"},
        )
    )

    return {
        "schema_version": "1.0.0",
        "packet_class": packet_class,
        "consumer_identity": consumer_identity.strip(),
        "permission_context": permission_context,
        "permission_context_digest": sha256_hex(canonical_json(permission_context)),
        "compile_input": compile_input,
        "retrieval_input": retrieval_input,
        "retrieval_goal": request.get("retrieval_goal") or request.get("user_goal"),
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
            "runtime_version": request.get("runtime_version", "slice_06"),
            "corpus_version": request.get("corpus_version", "starter"),
            "budget_version": request.get("budget_version", "v1_lock"),
            "compatibility_posture": "compatible",
        },
        "vector_backend_available": bool(request.get("vector_backend_available", False)),
        "reranker_available": bool(request.get("reranker_available", True)),
        "pruning_available": bool(request.get("pruning_available", True)),
        "cache_available": bool(request.get("cache_available", True)),
        "allow_minimum_viable_packet": allow_minimum_viable_packet,
        "simulate_retrieval_ms": int(request.get("simulate_retrieval_ms", 0)),
        "simulate_rerank_prune_ms": int(request.get("simulate_rerank_prune_ms", 0)),
        "simulate_compile_validate_ms": int(request.get("simulate_compile_validate_ms", 0)),
        "execution_mode": execution_mode,
        "adapter_config": adapter_config,
        "live_query": live_query,
        "cache_key": request.get("cache_key"),
        "cache_enabled": bool(request.get("cache_enabled", True)),
        "emit_telemetry": bool(request.get("emit_telemetry", True)),
        "telemetry_dir": request.get("telemetry_dir", "harness/telemetry"),
        "evidence_dir": request.get("evidence_dir", "harness/evidence"),
    }
