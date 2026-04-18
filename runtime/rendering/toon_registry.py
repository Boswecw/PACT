from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from runtime.rendering.renderer import RenderFailure


REGISTRY_FILENAME = "toon_registry.json"


@lru_cache(maxsize=1)
def load_wave1_registry() -> dict[str, Any]:
    registry_path = Path(__file__).resolve().with_name(REGISTRY_FILENAME)
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenderFailure(
            "TOON registry file is missing",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="registry_load_failure",
        ) from exc
    except json.JSONDecodeError as exc:
        raise RenderFailure(
            "TOON registry file is invalid JSON",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="registry_load_failure",
        ) from exc

    required_fields = {
        "schema_version",
        "segment_version",
        "row_definition_id",
        "supported_packet_classes",
        "field_order",
    }
    missing = required_fields.difference(payload)
    if missing:
        raise RenderFailure(
            f"TOON registry is missing required fields: {sorted(missing)}",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="registry_load_failure",
        )

    if payload["row_definition_id"] != "ranked_result_row_v1":
        raise RenderFailure(
            "TOON registry row_definition_id is unsupported in wave 1",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="registry_load_failure",
        )

    if payload["field_order"] != ["rank", "title", "source_ref", "summary"]:
        raise RenderFailure(
            "TOON registry field order is unsupported in wave 1",
            public_reason_code="serialization_failed",
            failure_state="render_failure",
            fallback_allowed=False,
            fallback_reason="registry_load_failure",
        )

    return payload
