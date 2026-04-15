from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def emit_runtime_report(
    root_dir: str | Path,
    telemetry_dir: str,
    request_id: str,
    receipt_id: str,
    payload: dict[str, Any],
) -> tuple[str, str]:
    root = Path(root_dir)
    out_dir = root / telemetry_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / f"slice_06_runtime_report_{receipt_id}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest_path = out_dir / "slice_06_manifest.json"
    manifest = _load_json(manifest_path, {"entries": []})
    entries = [entry for entry in manifest.get("entries", []) if entry.get("receipt_id") != receipt_id]
    entries.append(
        {
            "request_id": request_id,
            "receipt_id": receipt_id,
            "trace_id": payload.get("trace_id"),
            "result_kind": payload.get("result_kind"),
            "packet_class": payload.get("packet_class"),
            "telemetry_path": str(report_path),
        }
    )
    manifest["entries"] = entries
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return str(report_path), str(manifest_path)
