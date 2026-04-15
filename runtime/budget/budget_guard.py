from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.shared.pact_utils import estimate_token_count

BUDGETS = {
    "answer_packet": {
        "max_retrieval_ms": 350,
        "max_rerank_prune_ms": 250,
        "max_compile_validate_ms": 150,
        "max_total_overhead_ms": 750,
        "max_input_tokens": 3500,
        "min_reduction_percent": 35.0,
    },
    "policy_response_packet": {
        "max_retrieval_ms": 300,
        "max_rerank_prune_ms": 200,
        "max_compile_validate_ms": 150,
        "max_total_overhead_ms": 650,
        "max_input_tokens": 3000,
        "min_reduction_percent": 25.0,
    },
    "search_assist_packet": {
        "max_retrieval_ms": 400,
        "max_rerank_prune_ms": 300,
        "max_compile_validate_ms": 175,
        "max_total_overhead_ms": 875,
        "max_input_tokens": 4200,
        "min_reduction_percent": 35.0,
    },
}

STATE_PRIORITY = {
    "normal": 0,
    "cache_degraded": 1,
    "retrieval_degraded": 2,
    "rerank_degraded": 3,
    "pruning_degraded": 4,
    "minimum_viable_packet": 5,
    "safe_failure": 6,
}


@dataclass
class BudgetExceededError(Exception):
    message: str
    failure_state: str = "budget_failure"
    public_reason_code: str = "over_budget"

    def __str__(self) -> str:
        return self.message


def get_budget(packet_class: str) -> dict[str, Any]:
    return BUDGETS[packet_class]


def packet_token_count(packet: dict[str, Any]) -> int:
    return estimate_token_count(packet)


def reduce_compile_input_for_retry(packet_class: str, compile_input: dict[str, Any]) -> dict[str, Any]:
    reduced = dict(compile_input)
    if packet_class == "answer_packet":
        reduced["support_blocks"] = list(reduced.get("support_blocks", []))[:1]
        reduced["grounding_refs"] = list(reduced.get("grounding_refs", []))[:1]
    elif packet_class == "policy_response_packet":
        reduced["policy_statements"] = list(reduced.get("policy_statements", []))[:1]
        reduced["grounding_refs"] = list(reduced.get("grounding_refs", []))[:1]
    elif packet_class == "search_assist_packet":
        reduced["ranked_result_blocks"] = list(reduced.get("ranked_result_blocks", []))[:2]
        reduced["grounding_refs"] = list(reduced.get("grounding_refs", []))[:2]
        reduced["result_count"] = len(reduced["ranked_result_blocks"])
    return reduced


def choose_stricter_state(*states: str) -> str:
    chosen = "normal"
    for state in states:
        if STATE_PRIORITY.get(state, 0) > STATE_PRIORITY.get(chosen, 0):
            chosen = state
    return chosen
