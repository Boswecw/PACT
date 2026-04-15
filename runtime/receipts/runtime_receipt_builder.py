from __future__ import annotations

from typing import Any

from src.shared.pact_utils import build_source_lineage_digest, canonical_json, estimate_token_count, sha256_hex, stable_id


def build_runtime_receipt(
    normalized: dict[str, Any] | None,
    packet_or_failure: dict[str, Any],
    *,
    model_call_allowed: bool,
    safe_failure_invoked: bool,
    degradation_state: str,
    compile_validate_ms: int,
    retrieval_ms: int = 0,
    rerank_prune_ms: int = 0,
    input_tokens: int | None = None,
    naive_baseline_tokens: int | None = None,
) -> dict[str, Any]:
    normalized = normalized or {}
    packet_class = packet_or_failure.get("packet_class") or normalized.get("packet_class") or "answer_packet"
    request_id = packet_or_failure.get("request_id") or normalized.get("request_id") or stable_id("req", packet_or_failure)
    trace_id = packet_or_failure.get("trace_id") or normalized.get("trace_id") or stable_id("trace", packet_or_failure)
    packet_id = packet_or_failure.get("packet_id") or packet_or_failure.get("failure_packet_id") or stable_id("pkt", packet_or_failure)
    packet_hash = packet_or_failure.get("packet_hash") or packet_or_failure.get("_derived_hash") or sha256_hex(canonical_json(packet_or_failure))
    source_lineage_digest = normalized.get("source_lineage_digest") or build_source_lineage_digest(packet_or_failure, "request")
    serialization_profile = normalized.get("serialization_profile", "plain_text_only")
    version_set = normalized.get(
        "version_set",
        {
            "contract_version": "1.0.0",
            "runtime_version": "slice_04",
            "corpus_version": "starter",
            "budget_version": "v1_lock",
            "compatibility_posture": "compatible",
        },
    )

    measured_tokens = estimate_token_count(packet_or_failure)
    final_input_tokens = measured_tokens if input_tokens is None else input_tokens
    naive_tokens = final_input_tokens if naive_baseline_tokens is None else naive_baseline_tokens
    reduction_percentage = 0.0
    if naive_tokens > 0:
        reduction_percentage = max(0.0, round(((naive_tokens - final_input_tokens) / naive_tokens) * 100.0, 2))

    total_pact_overhead_ms = retrieval_ms + rerank_prune_ms + compile_validate_ms

    seed = {
        "request_id": request_id,
        "trace_id": trace_id,
        "packet_id": packet_id,
        "safe_failure_invoked": safe_failure_invoked,
        "degradation_state": degradation_state,
    }

    return {
        "schema_version": "1.0.0",
        "receipt_id": stable_id("rcpt", seed),
        "request_id": request_id,
        "trace_id": trace_id,
        "packet_id": packet_id,
        "packet_class": packet_class,
        "version_set": version_set,
        "retrieval_mode": normalized.get("retrieval_mode", "lexical_only"),
        "pruning_mode": normalized.get("pruning_mode", "none"),
        "serialization_profile": serialization_profile,
        "degradation_state": degradation_state,
        "source_lineage_digest": source_lineage_digest,
        "packet_hash": packet_hash,
        "token_counts": {
            "input_tokens": final_input_tokens,
            "naive_baseline_tokens": naive_tokens,
            "reduction_percentage": reduction_percentage,
        },
        "latency_breakdown": {
            "retrieval_ms": retrieval_ms,
            "rerank_prune_ms": rerank_prune_ms,
            "compile_validate_ms": compile_validate_ms,
            "total_pact_overhead_ms": total_pact_overhead_ms,
        },
        "model_call_allowed": model_call_allowed,
        "safe_failure_invoked": safe_failure_invoked,
    }
