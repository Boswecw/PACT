from __future__ import annotations

from pathlib import Path
from typing import Any

from .bundle_builder import build_export_bundle


def maybe_emit_control_plane_bundle(
    root_dir: str | Path,
    request: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, str]:
    config = request.get("control_plane_export") or {}
    enabled = bool(request.get("emit_control_plane_export", False) or config)
    if not enabled:
        return {}
    if not isinstance(config, dict):
        raise ValueError("control_plane_export must be an object when provided")

    export_dir = config.get("export_dir") or request.get("export_dir") or "harness/exports"
    package_label = config.get("package_label") or request.get("package_label") or "operator_replay"

    return build_export_bundle(
        root_dir,
        request=request,
        result=result,
        export_dir=export_dir,
        package_label=package_label,
    )
