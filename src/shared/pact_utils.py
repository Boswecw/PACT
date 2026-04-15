from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    if not isinstance(value, str):
        value = canonical_json(value)
    return f"{prefix}_{sha256_hex(value)[:16]}"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso_z(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def add_seconds_to_timestamp(timestamp: str, seconds: int) -> str:
    return (_parse_iso_z(timestamp) + timedelta(seconds=seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def estimate_token_count(value: Any) -> int:
    if not isinstance(value, str):
        value = canonical_json(value)
    rough = value.split()
    if not rough:
        return 0
    return max(1, int(round(len(rough) * 1.3)))


def ensure_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected a list")
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("list must contain only strings")
        cleaned.append(item)
    return cleaned


def build_source_lineage_digest(value: Any, source_scope: str = "request") -> dict[str, str]:
    return {
        "digest_algorithm": "sha256",
        "digest": sha256_hex(canonical_json(value)),
        "source_scope": source_scope,
    }
