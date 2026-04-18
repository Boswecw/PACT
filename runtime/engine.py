from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from runtime.adapters.factory import create_cache_provider, create_retrieval_provider
from runtime.adapters.interfaces import ProviderError
from runtime.budget.budget_guard import (
    choose_stricter_state,
    get_budget,
    packet_token_count,
    reduce_compile_input_for_retry,
)
from runtime.compiler.packet_compiler import PacketCompileError, compile_packet, compile_packet_legacy
from runtime.compiler.packet_base_builder import finalize_packet_hash
from runtime.compiler.safe_failure_builder import build_safe_failure_packet
from runtime.evidence.exporter import emit_evidence_bundle
from runtime.export.control_plane_adapter import maybe_emit_control_plane_bundle
from runtime.intake.request_normalizer import IntakeNormalizationError, normalize_request
from runtime.observability.toon_evidence import record_serialization_event
from runtime.receipts.runtime_receipt_builder import build_runtime_receipt
from runtime.rendering import RenderFailure, render_model_artifact, render_safe_failure_artifact
from runtime.retrieval.pruning_engine import (
    BudgetPreparationError,
    GroundingUnavailableError,
    prepare_compile_input,
)
from runtime.retrieval.retrieval_engine import execute_retrieval
from runtime.telemetry.emitter import emit_runtime_report
from runtime.validation.schema_validator import PacketValidationError, validate_instance


SCHEMA_MAP = {
    "answer_packet": "answer_packet.schema.json",
    "policy_response_packet": "policy_response_packet.schema.json",
    "search_assist_packet": "search_assist_packet.schema.json",
}
ROOT_DIR = Path(__file__).resolve().parents[1]


def _emit_artifacts(
    normalized: dict[str, Any],
    result_kind: str,
    packet: dict[str, Any],
    receipt: dict[str, Any],
    telemetry_context: dict[str, Any] | None,
    candidate_refs: list[str],
) -> dict[str, str]:
    payload = {
        "request_id": normalized["request_id"],
        "trace_id": normalized["trace_id"],
        "execution_mode": normalized.get("execution_mode", "replay"),
        "result_kind": result_kind,
        "packet_class": packet["packet_class"],
        "packet_id": packet.get("packet_id"),
        "receipt_id": receipt["receipt_id"],
        **(telemetry_context or {}),
    }
    telemetry_path, manifest_path = emit_runtime_report(
        ROOT_DIR,
        normalized["telemetry_dir"],
        normalized["request_id"],
        receipt["receipt_id"],
        payload,
    )
    evidence_payload = {
        "request_id": normalized["request_id"],
        "trace_id": normalized["trace_id"],
        "execution_mode": normalized["execution_mode"],
        "packet_class": packet["packet_class"],
        "packet_id": packet.get("packet_id"),
        "receipt_id": receipt["receipt_id"],
        "result_kind": result_kind,
        "candidate_refs": candidate_refs,
        "telemetry_path": telemetry_path,
        "manifest_path": manifest_path,
        "telemetry_context": telemetry_context or {},
    }
    evidence_path = emit_evidence_bundle(
        ROOT_DIR,
        normalized["evidence_dir"],
        receipt["receipt_id"],
        evidence_payload,
    )
    return {
        "telemetry_path": telemetry_path,
        "manifest_path": manifest_path,
        "evidence_path": evidence_path,
    }


def _merge_telemetry_context(
    base: dict[str, Any] | None,
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if base:
        merged.update(base)
    if extra:
        merged.update(extra)
    return merged


def _safe_failure_response(
    normalized: dict[str, Any] | None,
    source: dict[str, Any] | None,
    *,
    failure_state: str,
    public_reason_code: str,
    compile_validate_ms: int,
    retrieval_ms: int = 0,
    rerank_prune_ms: int = 0,
    degradation_state: str = "safe_failure",
    naive_baseline_tokens: int | None = None,
    telemetry_context: dict[str, Any] | None = None,
    candidate_refs: list[str] | None = None,
    render_attempted: bool = False,
) -> dict[str, Any]:
    safe_failure = build_safe_failure_packet(
        normalized or source,
        failure_state=failure_state,
        public_reason_code=public_reason_code,
    )
    validate_instance({k: v for k, v in safe_failure.items() if not k.startswith("_")}, "safe_failure_packet.schema.json")
    rendered_artifact = render_safe_failure_artifact(
        normalized,
        safe_failure,
        render_attempted=render_attempted,
        fallback_reason=public_reason_code,
    )
    receipt = build_runtime_receipt(
        normalized,
        safe_failure,
        model_call_allowed=False,
        safe_failure_invoked=True,
        degradation_state=degradation_state,
        compile_validate_ms=compile_validate_ms,
        retrieval_ms=retrieval_ms,
        rerank_prune_ms=rerank_prune_ms,
        naive_baseline_tokens=naive_baseline_tokens,
        input_tokens=rendered_artifact.after_tokens,
        serialization_evidence=rendered_artifact.to_serialization_evidence(),
    )
    validate_instance(receipt, "runtime_receipt.schema.json")
    safe_failure.pop("_derived_hash", None)
    result = {
        "ok": False,
        "packet": safe_failure,
        "receipt": receipt,
        "artifact_text": rendered_artifact.artifact_text,
        "artifact_kind": rendered_artifact.artifact_kind,
        "artifact_hash": rendered_artifact.artifact_hash,
        "model_artifact_emitted": False,
    }
    if normalized and normalized.get("emit_telemetry", False):
        result.update(
            _emit_artifacts(
                normalized,
                "safe_failure",
                safe_failure,
                receipt,
                telemetry_context,
                candidate_refs or [],
            )
        )
    try:
        evidence = receipt.get("serialization_evidence", {})
        record_serialization_event(
            packet_class=safe_failure.get("packet_class"),
            request_id=safe_failure.get("request_id"),
            trace_id=safe_failure.get("trace_id"),
            requested_profile=evidence.get("requested_profile"),
            used_profile=evidence.get("used_profile"),
            render_attempted=bool(evidence.get("render_attempted")),
            fallback_used=bool(evidence.get("fallback_used")),
            fallback_reason=evidence.get("fallback_reason"),
            artifact_kind=evidence.get("artifact_kind"),
            ok=False,
            model_artifact_emitted=False,
        )
    except Exception:
        pass
    return result


def _success_response(
    normalized: dict[str, Any],
    packet: dict[str, Any],
    *,
    degradation_state: str,
    compile_validate_ms: int,
    retrieval_ms: int = 0,
    rerank_prune_ms: int = 0,
    naive_baseline_tokens: int | None = None,
    telemetry_context: dict[str, Any] | None = None,
    candidate_refs: list[str] | None = None,
) -> dict[str, Any]:
    packet["lifecycle_state"] = "admitted"
    packet["admissibility_state"] = "admissible"
    finalize_packet_hash(packet)
    validate_instance(packet, SCHEMA_MAP[packet["packet_class"]])

    try:
        rendered_artifact = render_model_artifact(packet, normalized["serialization_profile"])
    except RenderFailure as exc:
        return _safe_failure_response(
            normalized,
            packet,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=compile_validate_ms,
            retrieval_ms=retrieval_ms,
            rerank_prune_ms=rerank_prune_ms,
            naive_baseline_tokens=naive_baseline_tokens,
            telemetry_context=_merge_telemetry_context(
                telemetry_context,
                {
                    "serialization_requested_profile": normalized["serialization_profile"],
                    "render_failure_reason": exc.fallback_reason or exc.public_reason_code,
                },
            ),
            candidate_refs=candidate_refs,
            render_attempted=True,
        )

    receipt = build_runtime_receipt(
        normalized,
        packet,
        model_call_allowed=True,
        safe_failure_invoked=False,
        degradation_state=degradation_state,
        compile_validate_ms=compile_validate_ms,
        retrieval_ms=retrieval_ms,
        rerank_prune_ms=rerank_prune_ms,
        input_tokens=rendered_artifact.after_tokens,
        naive_baseline_tokens=rendered_artifact.before_tokens if naive_baseline_tokens is None else naive_baseline_tokens,
        serialization_evidence=rendered_artifact.to_serialization_evidence(),
    )
    validate_instance(receipt, "runtime_receipt.schema.json")
    result = {
        "ok": True,
        "packet": packet,
        "receipt": receipt,
        "artifact_text": rendered_artifact.artifact_text,
        "artifact_kind": rendered_artifact.artifact_kind,
        "artifact_hash": rendered_artifact.artifact_hash,
        "model_artifact_emitted": True,
    }
    if normalized.get("emit_telemetry", False):
        result.update(
            _emit_artifacts(
                normalized,
                "success",
                packet,
                receipt,
                _merge_telemetry_context(
                    telemetry_context,
                    {
                        "serialization_requested_profile": rendered_artifact.requested_profile,
                        "serialization_used_profile": rendered_artifact.used_profile,
                        "serialization_artifact_kind": rendered_artifact.artifact_kind,
                        "serialization_fallback_used": rendered_artifact.fallback_used,
                    },
                ),
                candidate_refs or [],
            )
        )
    try:
        evidence = receipt.get("serialization_evidence", {})
        record_serialization_event(
            packet_class=packet.get("packet_class"),
            request_id=packet.get("request_id"),
            trace_id=packet.get("trace_id"),
            requested_profile=evidence.get("requested_profile"),
            used_profile=evidence.get("used_profile"),
            render_attempted=bool(evidence.get("render_attempted")),
            fallback_used=bool(evidence.get("fallback_used")),
            fallback_reason=evidence.get("fallback_reason"),
            artifact_kind=evidence.get("artifact_kind"),
            ok=True,
            model_artifact_emitted=True,
        )
    except Exception:
        pass
    return result


def _direct_compile_pipeline(normalized: dict[str, Any], source_request: dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()
    try:
        packet = compile_packet_legacy(normalized)
        validate_instance(packet, SCHEMA_MAP[packet["packet_class"]])
    except PacketCompileError as exc:
        elapsed = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            normalized,
            source_request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
        )
    except PacketValidationError as exc:
        elapsed = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            normalized,
            source_request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
        )

    elapsed = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - start) * 1000))
    return _success_response(
        normalized,
        packet,
        degradation_state="normal",
        compile_validate_ms=elapsed,
    )


def _run_packet_pipeline(
    normalized: dict[str, Any],
    request: dict[str, Any],
    *,
    adapter_context: dict[str, Any],
) -> dict[str, Any]:
    budget = get_budget(normalized["packet_class"])
    candidate_refs = [item.get("source_ref") for item in normalized.get("retrieval_input", [])]

    retrieval_result = execute_retrieval(normalized)
    normalized["retrieval_mode"] = retrieval_result.retrieval_mode_used
    candidate_refs = [item.get("source_ref") for item in retrieval_result.candidates]

    if retrieval_result.retrieval_ms > budget["max_retrieval_ms"]:
        return _safe_failure_response(
            normalized,
            request,
            failure_state="budget_failure",
            public_reason_code="over_budget",
            compile_validate_ms=0,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=0,
            naive_baseline_tokens=0,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    try:
        prep = prepare_compile_input(normalized, retrieval_result)
    except GroundingUnavailableError as exc:
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=0,
            naive_baseline_tokens=0,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )
    except BudgetPreparationError as exc:
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=normalized.get("simulate_rerank_prune_ms", 0),
            naive_baseline_tokens=0,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    if prep.rerank_prune_ms > budget["max_rerank_prune_ms"]:
        return _safe_failure_response(
            normalized,
            request,
            failure_state="budget_failure",
            public_reason_code="over_budget",
            compile_validate_ms=0,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=prep.rerank_prune_ms,
            naive_baseline_tokens=prep.naive_baseline_tokens,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    normalized["compile_input"] = prep.compile_input

    compile_start = perf_counter()
    try:
        packet = compile_packet(normalized)
        validate_instance(packet, SCHEMA_MAP[packet["packet_class"]])
    except PacketCompileError as exc:
        elapsed = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - compile_start) * 1000))
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=prep.rerank_prune_ms,
            naive_baseline_tokens=prep.naive_baseline_tokens,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )
    except PacketValidationError as exc:
        elapsed = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - compile_start) * 1000))
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=prep.rerank_prune_ms,
            naive_baseline_tokens=prep.naive_baseline_tokens,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    compile_validate_ms = normalized.get("simulate_compile_validate_ms") or int(round((perf_counter() - compile_start) * 1000))
    if compile_validate_ms > budget["max_compile_validate_ms"]:
        return _safe_failure_response(
            normalized,
            request,
            failure_state="budget_failure",
            public_reason_code="over_budget",
            compile_validate_ms=compile_validate_ms,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=prep.rerank_prune_ms,
            naive_baseline_tokens=prep.naive_baseline_tokens,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    total_overhead_ms = retrieval_result.retrieval_ms + prep.rerank_prune_ms + compile_validate_ms
    if total_overhead_ms > budget["max_total_overhead_ms"]:
        return _safe_failure_response(
            normalized,
            request,
            failure_state="budget_failure",
            public_reason_code="over_budget",
            compile_validate_ms=compile_validate_ms,
            retrieval_ms=retrieval_result.retrieval_ms,
            rerank_prune_ms=prep.rerank_prune_ms,
            naive_baseline_tokens=prep.naive_baseline_tokens,
            telemetry_context=adapter_context,
            candidate_refs=candidate_refs,
        )

    final_tokens = packet_token_count(packet)
    if final_tokens > budget["max_input_tokens"]:
        reduced_compile_input = reduce_compile_input_for_retry(normalized["packet_class"], normalized["compile_input"])
        normalized["compile_input"] = reduced_compile_input
        try:
            retry_packet = compile_packet(normalized)
            validate_instance(retry_packet, SCHEMA_MAP[retry_packet["packet_class"]])
        except (PacketCompileError, PacketValidationError):
            return _safe_failure_response(
                normalized,
                request,
                failure_state="budget_failure",
                public_reason_code="over_budget",
                compile_validate_ms=compile_validate_ms,
                retrieval_ms=retrieval_result.retrieval_ms,
                rerank_prune_ms=prep.rerank_prune_ms,
                naive_baseline_tokens=prep.naive_baseline_tokens,
                telemetry_context=adapter_context,
                candidate_refs=candidate_refs,
            )
        retry_tokens = packet_token_count(retry_packet)
        if retry_tokens > budget["max_input_tokens"]:
            return _safe_failure_response(
                normalized,
                request,
                failure_state="budget_failure",
                public_reason_code="over_budget",
                compile_validate_ms=compile_validate_ms,
                retrieval_ms=retrieval_result.retrieval_ms,
                rerank_prune_ms=prep.rerank_prune_ms,
                naive_baseline_tokens=prep.naive_baseline_tokens,
                telemetry_context=adapter_context,
                candidate_refs=candidate_refs,
            )
        packet = retry_packet
        prep.degradation_state = choose_stricter_state(prep.degradation_state, "minimum_viable_packet")

    success_state = prep.degradation_state
    if not normalized["cache_available"]:
        success_state = choose_stricter_state(success_state, "cache_degraded")

    return _success_response(
        normalized,
        packet,
        degradation_state=success_state,
        compile_validate_ms=compile_validate_ms,
        retrieval_ms=retrieval_result.retrieval_ms,
        rerank_prune_ms=prep.rerank_prune_ms,
        naive_baseline_tokens=prep.naive_baseline_tokens,
        telemetry_context=adapter_context,
        candidate_refs=candidate_refs,
    )


def execute_slice_03(request: dict[str, Any]) -> dict[str, Any]:
    try:
        normalized = normalize_request(request)
    except IntakeNormalizationError as exc:
        return _safe_failure_response(
            None,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
        )
    return _direct_compile_pipeline(normalized, request)


def execute_slice_04(request: dict[str, Any]) -> dict[str, Any]:
    try:
        normalized = normalize_request(request)
    except IntakeNormalizationError as exc:
        return _safe_failure_response(
            None,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
        )

    if "retrieval_input" not in request:
        return _direct_compile_pipeline(normalized, request)

    return _run_packet_pipeline(
        normalized,
        request,
        adapter_context={"execution_mode": "replay", "retrieval_provider_id": "slice_04_inline", "cache_status": "bypassed"},
    )


def _execute_live_or_replay(request: dict[str, Any]) -> dict[str, Any]:
    try:
        normalized = normalize_request(request)
    except IntakeNormalizationError as exc:
        return _safe_failure_response(
            None,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
        )

    if normalized["execution_mode"] == "replay" and "retrieval_input" not in request:
        return _direct_compile_pipeline(normalized, request)

    try:
        retrieval_provider = create_retrieval_provider(normalized)
        cache_provider = create_cache_provider(normalized)
    except ProviderError as exc:
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=0,
            telemetry_context={"execution_mode": normalized["execution_mode"], "cache_status": "provider_error"},
        )

    cache_status = "bypassed"
    if normalized.get("cache_key"):
        try:
            cached = cache_provider.get(normalized["cache_key"])
            if cached is not None:
                normalized["retrieval_input"] = list(cached)
                cache_status = "hit"
            else:
                normalized["retrieval_input"] = retrieval_provider.search(normalized["live_query"], request)
                cache_provider.set(normalized["cache_key"], list(normalized["retrieval_input"]))
                cache_status = "miss"
        except ProviderError:
            normalized["retrieval_input"] = retrieval_provider.search(normalized["live_query"], request)
            cache_status = "degraded"
            normalized["cache_available"] = False
    else:
        try:
            normalized["retrieval_input"] = retrieval_provider.search(normalized["live_query"], request)
        except ProviderError as exc:
            return _safe_failure_response(
                normalized,
                request,
                failure_state=exc.failure_state,
                public_reason_code=exc.public_reason_code,
                compile_validate_ms=0,
                telemetry_context={"execution_mode": normalized["execution_mode"], "cache_status": "bypassed"},
            )

    adapter_context = {
        "execution_mode": normalized["execution_mode"],
        "retrieval_provider_id": retrieval_provider.provider_id,
        "cache_provider_id": cache_provider.provider_id,
        "cache_status": cache_status,
        "retrieved_candidate_count": len(normalized["retrieval_input"]),
    }
    return _run_packet_pipeline(normalized, request, adapter_context=adapter_context)


def execute_slice_05(request: dict[str, Any]) -> dict[str, Any]:
    return _execute_live_or_replay(request)


def execute_slice_06(request: dict[str, Any]) -> dict[str, Any]:
    return _execute_live_or_replay(request)


def execute_slice_07(request: dict[str, Any]) -> dict[str, Any]:
    result = execute_slice_06(request)
    try:
        export_artifacts = maybe_emit_control_plane_bundle(ROOT_DIR, request, result)
    except Exception as exc:  # pragma: no cover - bounded export hardening surface
        result["control_plane_export_ok"] = False
        result["control_plane_export_error"] = str(exc)
        return result

    if export_artifacts:
        result.update(export_artifacts)
        result["control_plane_export_ok"] = True

    return result
