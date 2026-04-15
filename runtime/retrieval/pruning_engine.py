from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from src.shared.pact_utils import estimate_token_count, stable_id


AUTHORITY_ORDER = {"primary": 3, "secondary": 2, "derived": 1}
BUDGETS = {
    "answer_packet": {"max_input_tokens": 3500},
    "policy_response_packet": {"max_input_tokens": 3000},
    "search_assist_packet": {"max_input_tokens": 4200},
}


@dataclass
class GroundingUnavailableError(Exception):
    message: str
    failure_state: str = "grounding_failure"
    public_reason_code: str = "grounding_unavailable"

    def __str__(self) -> str:
        return self.message


@dataclass
class BudgetPreparationError(Exception):
    message: str
    failure_state: str = "budget_failure"
    public_reason_code: str = "over_budget"

    def __str__(self) -> str:
        return self.message


@dataclass
class PreparationResult:
    compile_input: dict[str, Any]
    rerank_prune_ms: int
    degradation_state: str
    naive_baseline_tokens: int
    candidate_count: int


def _candidate_excerpt(candidate: dict[str, Any]) -> str:
    content = candidate.get("content", "")
    return content[:240]


def _grounding_ref(candidate: dict[str, Any], idx: int) -> dict[str, Any]:
    excerpt = _candidate_excerpt(candidate)
    return {
        "grounding_id": stable_id("g", {"source_ref": candidate["source_ref"], "idx": idx}),
        "source_ref": candidate["source_ref"],
        "authority_class": candidate.get("authority_class", "secondary"),
        "excerpt": excerpt,
        "start_offset": 0,
        "end_offset": len(excerpt),
    }


def _naive_baseline_tokens(compile_input: dict[str, Any], candidates: list[dict[str, Any]]) -> int:
    baseline_payload = {
        "strategy": "naive_full_context",
        "compile_input": compile_input,
        "retrieval_input": candidates,
    }
    return estimate_token_count(baseline_payload)


def prepare_compile_input(normalized: dict[str, Any], retrieval_result: Any) -> PreparationResult:
    start = perf_counter()
    compile_input = dict(normalized["compile_input"])
    packet_class = normalized["packet_class"]
    budget_limit = BUDGETS[packet_class]["max_input_tokens"]
    preassembly_limit = int(budget_limit * 0.8)
    candidates = list(retrieval_result.candidates)
    naive_tokens = _naive_baseline_tokens(compile_input, candidates)
    degradation_state = retrieval_result.degradation_state

    if not candidates and normalized["grounding_required"]:
        raise GroundingUnavailableError("no retrieval candidates were available for grounding")

    if candidates:
        if normalized["reranker_available"]:
            candidates.sort(
                key=lambda item: (
                    AUTHORITY_ORDER.get(item.get("authority_class", "secondary"), 0),
                    item.get("lexical_score", 0.0) + item.get("vector_score", 0.0),
                ),
                reverse=True,
            )
        else:
            if degradation_state == "normal":
                degradation_state = "rerank_degraded"

        if normalized["pruning_available"]:
            selected: list[dict[str, Any]] = []
            running_tokens = estimate_token_count(compile_input)
            for candidate in candidates:
                candidate_tokens = estimate_token_count(candidate.get("content", ""))
                if selected and running_tokens + candidate_tokens > preassembly_limit:
                    break
                selected.append(candidate)
                running_tokens += candidate_tokens
            candidates = selected or candidates[:1]
        else:
            total_tokens = estimate_token_count("\n".join(candidate.get("content", "") for candidate in candidates))
            if total_tokens <= preassembly_limit and normalized["allow_minimum_viable_packet"]:
                degradation_state = "minimum_viable_packet"
            else:
                raise BudgetPreparationError("pruning unavailable and candidate set exceeds minimum viable rules")

        grounding_refs = [_grounding_ref(candidate, idx) for idx, candidate in enumerate(candidates, start=1)]

        if packet_class == "answer_packet":
            compile_input["task_goal"] = compile_input.get("task_goal") or normalized.get("retrieval_goal") or "Answer the request using selected sources."
            compile_input["instruction_block"] = compile_input.get("instruction_block") or "Use only selected grounded material."
            compile_input["support_blocks"] = compile_input.get("support_blocks", []) + [_candidate_excerpt(candidate) for candidate in candidates]
            compile_input["grounding_refs"] = grounding_refs
            compile_input["answer_constraints"] = compile_input.get("answer_constraints", [])
        elif packet_class == "policy_response_packet":
            compile_input["policy_scope"] = compile_input.get("policy_scope") or normalized.get("retrieval_goal") or "policy_response"
            compile_input["policy_statements"] = compile_input.get("policy_statements", []) + [_candidate_excerpt(candidate) for candidate in candidates]
            compile_input["required_cautions"] = compile_input.get("required_cautions", ["Return only grounded policy guidance."])
            compile_input["grounding_refs"] = grounding_refs
            compile_input["disallowed_answer_modes"] = compile_input.get("disallowed_answer_modes", [])
        else:
            compile_input["search_goal"] = compile_input.get("search_goal") or normalized.get("retrieval_goal") or "Rank grounded results."
            compile_input["ranked_result_blocks"] = [
                {
                    "rank": idx,
                    "title": candidate.get("title", candidate["source_ref"]),
                    "source_ref": candidate["source_ref"],
                    "summary": _candidate_excerpt(candidate),
                }
                for idx, candidate in enumerate(candidates, start=1)
            ]
            compile_input["selection_constraints"] = compile_input.get("selection_constraints", [])
            compile_input["grounding_refs"] = grounding_refs
            compile_input["result_count"] = len(compile_input["ranked_result_blocks"])

    measured_ms = int(round((perf_counter() - start) * 1000))
    rerank_prune_ms = normalized.get("simulate_rerank_prune_ms") or measured_ms
    return PreparationResult(
        compile_input=compile_input,
        rerank_prune_ms=rerank_prune_ms,
        degradation_state=degradation_state,
        naive_baseline_tokens=naive_tokens,
        candidate_count=len(candidates),
    )
