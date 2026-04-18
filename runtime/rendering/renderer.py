from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from src.shared.pact_utils import canonical_json, estimate_token_count, sha256_hex, stable_id

TOKEN_ESTIMATOR_FAMILY = "pact_estimate_token_count_v1"


@dataclass
class RenderFailure(Exception):
    message: str
    public_reason_code: str = "serialization_failed"
    failure_state: str = "render_failure"
    fallback_allowed: bool = False
    fallback_reason: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class RenderedArtifact:
    requested_profile: str
    used_profile: str
    render_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    artifact_kind: str
    artifact_version: str
    artifact_text: str
    segment_meta: dict[str, Any] | None
    before_tokens: int
    after_tokens: int
    estimator_family: str = TOKEN_ESTIMATOR_FAMILY

    @property
    def artifact_hash(self) -> str:
        return f"sha256:{sha256_hex(self.artifact_text)}"

    def to_serialization_evidence(self) -> dict[str, Any]:
        delta_tokens = self.before_tokens - self.after_tokens
        reduction_percentage = 0.0
        if self.before_tokens > 0:
            reduction_percentage = round((delta_tokens / self.before_tokens) * 100.0, 2)

        evidence = {
            "schema_version": "1.0.0",
            "requested_profile": self.requested_profile,
            "used_profile": self.used_profile,
            "render_attempted": self.render_attempted,
            "fallback_used": self.fallback_used,
            "artifact_kind": self.artifact_kind,
            "artifact_version": self.artifact_version,
            "artifact_hash": self.artifact_hash,
            "segment_meta": self.segment_meta,
            "token_estimates": {
                "before_tokens": self.before_tokens,
                "after_tokens": self.after_tokens,
                "delta_tokens": delta_tokens,
                "reduction_percentage": reduction_percentage,
                "estimator_family": self.estimator_family,
            },
        }
        if self.fallback_used and self.fallback_reason:
            evidence["fallback_reason"] = self.fallback_reason
        return evidence


def _toon_wave1_enabled() -> bool:
    raw = os.getenv("PACT_ENABLE_TOON_WAVE1", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def render_model_artifact(packet: dict[str, Any], requested_profile: str) -> RenderedArtifact:
    if requested_profile == "plain_text_only":
        artifact_text = _render_plain_text_only(packet)
        tokens = estimate_token_count(artifact_text)
        return RenderedArtifact(
            requested_profile=requested_profile,
            used_profile="plain_text_only",
            render_attempted=False,
            fallback_used=False,
            fallback_reason=None,
            artifact_kind="plain_text",
            artifact_version="1.0.0",
            artifact_text=artifact_text,
            segment_meta=None,
            before_tokens=tokens,
            after_tokens=tokens,
        )

    if requested_profile == "plain_text_with_compact_fields":
        artifact_text = _render_compact_fields(packet)
        tokens = estimate_token_count(artifact_text)
        return RenderedArtifact(
            requested_profile=requested_profile,
            used_profile="plain_text_with_compact_fields",
            render_attempted=False,
            fallback_used=False,
            fallback_reason=None,
            artifact_kind="plain_text",
            artifact_version="1.0.0",
            artifact_text=artifact_text,
            segment_meta=None,
            before_tokens=tokens,
            after_tokens=tokens,
        )

    if requested_profile == "plain_text_with_json_segment":
        artifact_text = _render_plain_text_with_json_segment(packet)
        tokens = estimate_token_count(artifact_text)
        return RenderedArtifact(
            requested_profile=requested_profile,
            used_profile="plain_text_with_json_segment",
            render_attempted=False,
            fallback_used=False,
            fallback_reason=None,
            artifact_kind="plain_text",
            artifact_version="1.0.0",
            artifact_text=artifact_text,
            segment_meta=None,
            before_tokens=tokens,
            after_tokens=tokens,
        )

    if requested_profile != "plain_text_with_toon_segment":
        raise RenderFailure(
            f"unsupported serialization profile: {requested_profile}",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
        )

    if not _toon_wave1_enabled():
        baseline_text = _render_plain_text_only(packet)
        baseline_tokens = estimate_token_count(baseline_text)
        return RenderedArtifact(
            requested_profile=requested_profile,
            used_profile="plain_text_only",
            render_attempted=False,
            fallback_used=True,
            fallback_reason="toon_disabled",
            artifact_kind="plain_text",
            artifact_version="1.0.0",
            artifact_text=baseline_text,
            segment_meta=None,
            before_tokens=baseline_tokens,
            after_tokens=baseline_tokens,
        )

    return _render_toon_or_fallback(packet, requested_profile)

def render_safe_failure_artifact(
    normalized: dict[str, Any] | None,
    packet_or_failure: dict[str, Any],
    *,
    render_attempted: bool = False,
    fallback_reason: str | None = None,
) -> RenderedArtifact:
    requested_profile = (normalized or {}).get("serialization_profile", "plain_text_only")
    artifact_text = _render_plain_text_only(packet_or_failure)
    tokens = estimate_token_count(artifact_text)
    return RenderedArtifact(
        requested_profile=requested_profile,
        used_profile=requested_profile if not fallback_reason else "plain_text_only",
        render_attempted=render_attempted,
        fallback_used=False,
        fallback_reason=None,
        artifact_kind="plain_text",
        artifact_version="1.0.0",
        artifact_text=artifact_text,
        segment_meta=None,
        before_tokens=tokens,
        after_tokens=tokens,
    )

def _render_toon_or_fallback(packet: dict[str, Any], requested_profile: str) -> RenderedArtifact:
    from runtime.rendering.toon_registry import load_wave1_registry

    registry = load_wave1_registry()
    packet_class = packet.get("packet_class")
    if packet_class not in set(registry.get("supported_packet_classes", [])):
        raise RenderFailure(
            f"TOON is not allowed for packet_class={packet_class!r} in wave 1",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="unsupported_packet_class",
        )

    baseline_text = _render_plain_text_only(packet)
    baseline_tokens = estimate_token_count(baseline_text)

    rows = packet.get("ranked_result_blocks")
    if not isinstance(rows, list) or not rows:
        return _build_toon_fallback_result(
            packet,
            requested_profile=requested_profile,
            baseline_text=baseline_text,
            baseline_tokens=baseline_tokens,
            fallback_reason="no_renderable_rows",
        )

    try:
        segment_text = _render_toon_segment(rows)
    except RenderFailure as exc:
        if exc.fallback_allowed:
            return _build_toon_fallback_result(
                packet,
                requested_profile=requested_profile,
                baseline_text=baseline_text,
                baseline_tokens=baseline_tokens,
                fallback_reason=exc.fallback_reason or "render_failure",
                render_attempted=True,
            )
        raise

    source_digest = packet.get("source_lineage_digest", {}).get("digest")
    source_lineage_digest = f"sha256:{source_digest}" if isinstance(source_digest, str) and source_digest else "sha256:" + sha256_hex(canonical_json(packet))
    segment_hash = f"sha256:{sha256_hex(segment_text)}"
    row_count = len(rows)
    segment_meta = {
        "segment_id": stable_id(
            "toonseg",
            {
                "packet_id": packet.get("packet_id"),
                "packet_hash": packet.get("packet_hash"),
                "row_definition_id": registry["row_definition_id"],
                "segment_hash": segment_hash,
            },
        ),
        "segment_version": registry["segment_version"],
        "row_definition_id": registry["row_definition_id"],
        "row_count": row_count,
        "source_lineage_digest": source_lineage_digest,
        "segment_hash": segment_hash,
    }

    after_tokens = estimate_token_count(segment_text)
    return RenderedArtifact(
        requested_profile=requested_profile,
        used_profile="plain_text_with_toon_segment",
        render_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        artifact_kind="toon_segment",
        artifact_version=registry["segment_version"],
        artifact_text=segment_text,
        segment_meta=segment_meta,
        before_tokens=baseline_tokens,
        after_tokens=after_tokens,
    )

def _build_toon_fallback_result(
    packet: dict[str, Any],
    *,
    requested_profile: str,
    baseline_text: str,
    baseline_tokens: int,
    fallback_reason: str,
    render_attempted: bool = True,
) -> RenderedArtifact:
    return RenderedArtifact(
        requested_profile=requested_profile,
        used_profile="plain_text_only",
        render_attempted=render_attempted,
        fallback_used=True,
        fallback_reason=fallback_reason,
        artifact_kind="plain_text",
        artifact_version="1.0.0",
        artifact_text=baseline_text,
        segment_meta=None,
        before_tokens=baseline_tokens,
        after_tokens=baseline_tokens,
    )

def _render_toon_segment(rows: list[dict[str, Any]]) -> str:
    from runtime.rendering.toon_registry import load_wave1_registry

    registry = load_wave1_registry()
    field_order = tuple(registry["field_order"])

    row_lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise RenderFailure(
                f"ranked_result_blocks[{index}] must be an object",
                fallback_allowed=True,
                fallback_reason="missing_required_field",
            )

        rendered_fields: list[str] = []
        for field_name in field_order:
            if field_name not in row:
                raise RenderFailure(
                    f"ranked_result_blocks[{index}].{field_name} is missing",
                    fallback_allowed=True,
                    fallback_reason="missing_required_field",
                )
            value = row.get(field_name)
            if value is None:
                raise RenderFailure(
                    f"ranked_result_blocks[{index}].{field_name} is null",
                    fallback_allowed=True,
                    fallback_reason="non_nullable_null",
                )
            rendered_value = _normalize_toon_field_value(value, field_name)
            rendered_fields.append(f"{field_name}={rendered_value}")

        row_lines.append("ROW|" + "|".join(rendered_fields))

    header = (
        f"[TOON_SEGMENT|segment_version={registry['segment_version']}"
        f"|row_definition_id={registry['row_definition_id']}|row_count={len(rows)}]"
    )
    footer = "[/TOON_SEGMENT]"
    return "\n".join([header, *row_lines, footer])

def _normalize_toon_field_value(value: Any, field_name: str) -> str:
    if isinstance(value, bool):
        raw = "true" if value else "false"
    elif isinstance(value, (int, float)):
        raw = str(value)
    elif isinstance(value, str):
        raw = value
    else:
        raise RenderFailure(
            f"{field_name} contains a non-text value that wave 1 cannot render",
            fallback_allowed=True,
            fallback_reason="missing_required_field",
        )

    normalized = _normalize_text(raw)
    normalized = normalized.replace("\\", "\\\\")
    normalized = normalized.replace("|", "\\|")
    normalized = normalized.replace("=", "\\=")
    normalized = normalized.replace("[TOON_SEGMENT", "\\[TOON_SEGMENT")
    normalized = normalized.replace("[/TOON_SEGMENT]", "\\[/TOON_SEGMENT]")
    normalized = normalized.replace("ROW|", "ROW\\|")
    normalized = normalized.replace("\n", "\\n")
    return normalized

def _normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" ") for line in value.split("\n")]
    return "\n".join(lines)

def _render_plain_text_only(packet: dict[str, Any]) -> str:
    packet_class = packet.get("packet_class", "unknown")
    lines = [
        f"PACKET_CLASS: {packet_class}",
        f"REQUEST_ID: {packet.get('request_id', '')}",
        f"TRACE_ID: {packet.get('trace_id', '')}",
    ]

    if packet_class == "answer_packet":
        lines.extend(
            [
                f"TASK_GOAL: {_safe_text(packet.get('task_goal'))}",
                f"INSTRUCTION_BLOCK: {_safe_text(packet.get('instruction_block'))}",
                "SUPPORT_BLOCKS:",
                *_render_string_list(packet.get("support_blocks")),
                "ANSWER_CONSTRAINTS:",
                *_render_string_list(packet.get("answer_constraints")),
            ]
        )
    elif packet_class == "policy_response_packet":
        lines.extend(
            [
                f"POLICY_SCOPE: {_safe_text(packet.get('policy_scope'))}",
                "POLICY_STATEMENTS:",
                *_render_string_list(packet.get("policy_statements")),
                "REQUIRED_CAUTIONS:",
                *_render_string_list(packet.get("required_cautions")),
                "DISALLOWED_ANSWER_MODES:",
                *_render_string_list(packet.get("disallowed_answer_modes")),
            ]
        )
    elif packet_class == "search_assist_packet":
        lines.extend(
            [
                f"SEARCH_GOAL: {_safe_text(packet.get('search_goal'))}",
                f"RESULT_COUNT: {packet.get('result_count', 0)}",
                "RANKED_RESULT_BLOCKS:",
                *_render_ranked_results(packet.get("ranked_result_blocks")),
                "SELECTION_CONSTRAINTS:",
                *_render_string_list(packet.get("selection_constraints")),
            ]
        )
    else:
        public_reason = packet.get("public_reason_code")
        failure_state = packet.get("failure_state")
        if public_reason is not None:
            lines.append(f"PUBLIC_REASON_CODE: {_safe_text(public_reason)}")
        if failure_state is not None:
            lines.append(f"FAILURE_STATE: {_safe_text(failure_state)}")

    lines.append("GROUNDING_REFS:")
    lines.extend(_render_grounding_refs(packet.get("grounding_refs")))
    return "\n".join(_normalize_text(line) for line in lines)

def _render_compact_fields(packet: dict[str, Any]) -> str:
    compact = {
        "packet_class": packet.get("packet_class"),
        "request_id": packet.get("request_id"),
        "trace_id": packet.get("trace_id"),
    }
    packet_class = packet.get("packet_class")
    if packet_class == "answer_packet":
        compact["task_goal"] = packet.get("task_goal")
        compact["instruction_block"] = packet.get("instruction_block")
        compact["support_blocks"] = packet.get("support_blocks", [])
        compact["answer_constraints"] = packet.get("answer_constraints", [])
    elif packet_class == "policy_response_packet":
        compact["policy_scope"] = packet.get("policy_scope")
        compact["policy_statements"] = packet.get("policy_statements", [])
        compact["required_cautions"] = packet.get("required_cautions", [])
        compact["disallowed_answer_modes"] = packet.get("disallowed_answer_modes", [])
    elif packet_class == "search_assist_packet":
        compact["search_goal"] = packet.get("search_goal")
        compact["result_count"] = packet.get("result_count", 0)
        compact["selection_constraints"] = packet.get("selection_constraints", [])
        compact["ranked_result_blocks"] = packet.get("ranked_result_blocks", [])
    else:
        compact["public_reason_code"] = packet.get("public_reason_code")
        compact["failure_state"] = packet.get("failure_state")
    compact["grounding_refs"] = packet.get("grounding_refs", [])
    return canonical_json(compact)

def _render_plain_text_with_json_segment(packet: dict[str, Any]) -> str:
    baseline = _render_plain_text_only(packet)
    json_segment = canonical_json(packet)
    return "\n".join(
        [
            baseline,
            "[JSON_SEGMENT|segment_version=1.0.0]",
            json_segment,
            "[/JSON_SEGMENT]",
        ]
    )

def _render_string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["- (none)"]
    lines: list[str] = []
    for item in value:
        lines.append(f"- {_safe_text(item)}")
    return lines

def _render_grounding_refs(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["- (none)"]
    lines: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            lines.append(f"- {canonical_json(item)}")
            continue
        lines.append(
            "- "
            + canonical_json(
                {
                    "grounding_id": item.get("grounding_id"),
                    "source_ref": item.get("source_ref"),
                    "authority_class": item.get("authority_class"),
                    "excerpt": item.get("excerpt"),
                    "start_offset": item.get("start_offset"),
                    "end_offset": item.get("end_offset"),
                }
            )
        )
    return lines

def _render_ranked_results(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["- (none)"]
    lines: list[str] = []
    for row in value:
        if not isinstance(row, dict):
            lines.append(f"- {canonical_json(row)}")
            continue
        lines.append(
            "- "
            + f"rank={row.get('rank')} | title={_safe_text(row.get('title'))} "
            + f"| source_ref={_safe_text(row.get('source_ref'))} "
            + f"| summary={_safe_text(row.get('summary'))}"
        )
    return lines

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _normalize_text(value)
    return _normalize_text(str(value))
