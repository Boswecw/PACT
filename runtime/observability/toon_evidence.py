from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_EVENT_LINES = 1000


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def evidence_file_path() -> Path:
    return repo_root() / ".pact_local" / "toon_events.jsonl"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _trim_to_last_n_lines(path: Path, max_lines: int = MAX_EVENT_LINES) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= max_lines:
        return
    path.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")


def record_serialization_event(
    *,
    packet_class: str | None,
    request_id: str | None,
    trace_id: str | None,
    requested_profile: str | None,
    used_profile: str | None,
    render_attempted: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    artifact_kind: str | None,
    ok: bool,
    model_artifact_emitted: bool,
) -> None:
    event = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "packet_class": packet_class,
        "request_id": request_id,
        "trace_id": trace_id,
        "requested_profile": requested_profile,
        "used_profile": used_profile,
        "render_attempted": bool(render_attempted),
        "fallback_used": bool(fallback_used),
        "fallback_reason": fallback_reason,
        "artifact_kind": artifact_kind,
        "ok": bool(ok),
        "model_artifact_emitted": bool(model_artifact_emitted),
    }

    path = evidence_file_path()
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    _trim_to_last_n_lines(path)


def load_events() -> list[dict[str, Any]]:
    path = evidence_file_path()
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def summarize_events() -> dict[str, Any]:
    events = load_events()

    fallback_reason_counts = Counter()
    packet_class_counts = Counter()
    requested_profile_counts = Counter()
    used_profile_counts = Counter()

    toon_requested = 0
    toon_used = 0
    fallback_count = 0

    for event in events:
        packet_class_counts[event.get("packet_class")] += 1
        requested_profile_counts[event.get("requested_profile")] += 1
        used_profile_counts[event.get("used_profile")] += 1

        if event.get("requested_profile") == "plain_text_with_toon_segment":
            toon_requested += 1
        if event.get("used_profile") == "plain_text_with_toon_segment":
            toon_used += 1
        if event.get("fallback_used"):
            fallback_count += 1
        reason = event.get("fallback_reason")
        if reason:
            fallback_reason_counts[reason] += 1

    return {
        "total_events": len(events),
        "toon_requested_count": toon_requested,
        "toon_used_count": toon_used,
        "fallback_count": fallback_count,
        "packet_class_counts": dict(packet_class_counts),
        "requested_profile_counts": dict(requested_profile_counts),
        "used_profile_counts": dict(used_profile_counts),
        "fallback_reason_counts": dict(fallback_reason_counts),
    }
