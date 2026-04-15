from __future__ import annotations

from time import perf_counter
from typing import Any

from runtime.compiler.packet_compiler import PacketCompileError, compile_packet
from runtime.compiler.packet_base_builder import finalize_packet_hash
from runtime.compiler.safe_failure_builder import build_safe_failure_packet
from runtime.intake.request_normalizer import IntakeNormalizationError, normalize_request
from runtime.receipts.runtime_receipt_builder import build_runtime_receipt
from runtime.validation.schema_validator import PacketValidationError, validate_instance


SCHEMA_MAP = {
    "answer_packet": "answer_packet.schema.json",
    "policy_response_packet": "policy_response_packet.schema.json",
    "search_assist_packet": "search_assist_packet.schema.json",
}


def _success_response(normalized: dict[str, Any], packet: dict[str, Any], compile_validate_ms: int) -> dict[str, Any]:
    packet["lifecycle_state"] = "admitted"
    packet["admissibility_state"] = "admissible"
    finalize_packet_hash(packet)
    validate_instance(packet, SCHEMA_MAP[packet["packet_class"]])

    receipt = build_runtime_receipt(
        normalized,
        packet,
        model_call_allowed=True,
        safe_failure_invoked=False,
        degradation_state="normal",
        compile_validate_ms=compile_validate_ms,
    )
    validate_instance(receipt, "runtime_receipt.schema.json")
    return {"ok": True, "packet": packet, "receipt": receipt}


def _safe_failure_response(
    normalized: dict[str, Any] | None,
    source: dict[str, Any] | None,
    *,
    failure_state: str,
    public_reason_code: str,
    compile_validate_ms: int,
) -> dict[str, Any]:
    safe_failure = build_safe_failure_packet(
        normalized or source,
        failure_state=failure_state,
        public_reason_code=public_reason_code,
    )
    validate_instance({k: v for k, v in safe_failure.items() if not k.startswith("_")}, "safe_failure_packet.schema.json")
    receipt = build_runtime_receipt(
        normalized,
        safe_failure,
        model_call_allowed=False,
        safe_failure_invoked=True,
        degradation_state="safe_failure",
        compile_validate_ms=compile_validate_ms,
    )
    validate_instance(receipt, "runtime_receipt.schema.json")
    safe_failure.pop("_derived_hash", None)
    return {"ok": False, "packet": safe_failure, "receipt": receipt}


def execute_slice_03(request: dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()

    try:
        normalized = normalize_request(request)
    except IntakeNormalizationError as exc:
        elapsed = int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            None,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
        )

    try:
        packet = compile_packet(normalized)
    except PacketCompileError as exc:
        elapsed = int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
        )
    except Exception:
        elapsed = int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            normalized,
            request,
            failure_state="compiler_failure",
            public_reason_code="validation_failed",
            compile_validate_ms=elapsed,
        )

    try:
        validate_instance(packet, SCHEMA_MAP[packet["packet_class"]])
    except PacketValidationError as exc:
        elapsed = int(round((perf_counter() - start) * 1000))
        return _safe_failure_response(
            normalized,
            request,
            failure_state=exc.failure_state,
            public_reason_code=exc.public_reason_code,
            compile_validate_ms=elapsed,
        )

    elapsed = int(round((perf_counter() - start) * 1000))
    return _success_response(normalized, packet, elapsed)
