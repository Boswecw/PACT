from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def emit_evidence_bundle(
    root_dir: str | Path,
    evidence_dir: str,
    receipt_id: str,
    payload: dict[str, Any],
) -> str:
    root = Path(root_dir)
    out_dir = root / evidence_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"slice_06_evidence_{receipt_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)
