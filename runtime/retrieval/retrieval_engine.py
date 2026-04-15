from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any


@dataclass
class RetrievalResult:
    candidates: list[dict[str, Any]]
    retrieval_mode_used: str
    degradation_state: str
    retrieval_ms: int


def execute_retrieval(normalized: dict[str, Any]) -> RetrievalResult:
    start = perf_counter()
    requested_mode = normalized["retrieval_mode"]
    vector_backend_available = normalized["vector_backend_available"]
    candidates = list(normalized["retrieval_input"])
    degradation_state = "normal"
    retrieval_mode_used = requested_mode

    if requested_mode == "hybrid" and not vector_backend_available:
        retrieval_mode_used = "lexical_only"
        degradation_state = "retrieval_degraded"
    elif requested_mode == "vector_only" and not vector_backend_available:
        retrieval_mode_used = "lexical_only"
        degradation_state = "retrieval_degraded"

    if retrieval_mode_used == "lexical_only":
        candidates.sort(key=lambda item: item.get("lexical_score", 0.0), reverse=True)
    elif retrieval_mode_used == "vector_only":
        candidates.sort(key=lambda item: item.get("vector_score", 0.0), reverse=True)
    else:
        candidates.sort(
            key=lambda item: item.get("lexical_score", 0.0) + item.get("vector_score", 0.0),
            reverse=True,
        )

    measured_ms = int(round((perf_counter() - start) * 1000))
    retrieval_ms = normalized.get("simulate_retrieval_ms") or measured_ms
    return RetrievalResult(
        candidates=candidates,
        retrieval_mode_used=retrieval_mode_used,
        degradation_state=degradation_state,
        retrieval_ms=retrieval_ms,
    )
