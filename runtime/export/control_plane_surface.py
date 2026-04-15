from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import canonical_json, sha256_hex, stable_id

from .operator_surface import build_export_catalog, get_export_bundle_detail, materialize_replay_package


def _filter_entries(entries: list[dict[str, Any]], query: dict[str, Any]) -> list[dict[str, Any]]:
    receipt_ids = set(query.get("receipt_ids") or [])
    packet_class = query.get("packet_class")
    result_kind = query.get("result_kind")
    package_label = query.get("package_label")

    filtered = []
    for entry in entries:
        if receipt_ids and entry["receipt_id"] not in receipt_ids:
            continue
        if packet_class and entry["packet_class"] != packet_class:
            continue
        if result_kind and entry["result_kind"] != result_kind:
            continue
        if package_label and entry["package_label"] != package_label:
            continue
        filtered.append(entry)
    return filtered


def _response_base(action: str, query: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "action": action,
        "ok": True,
        "query_digest": sha256_hex(canonical_json(query)),
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def query_export_surface(
    root_dir: str | Path,
    query: dict[str, Any],
    *,
    export_dir: str = "harness/exports",
    handoff_dir: str = "harness/handoffs",
) -> dict[str, Any]:
    root = Path(root_dir)
    action = query["action"]

    if action == "catalog":
        catalog = build_export_catalog(root, export_dir=export_dir)["catalog"]
        filtered = _filter_entries(catalog["entries"], query)
        response = {
            **_response_base(action, query),
            "result_count": len(filtered),
            "results": filtered,
        }
        validate_instance(response, "export_control_plane_response.schema.json")
        return response

    if action == "detail":
        detail = get_export_bundle_detail(root, query["receipt_id"], export_dir=export_dir)
        manifest = detail["manifest"]
        response = {
            **_response_base(action, query),
            "detail": {
                "receipt_id": manifest["receipt_id"],
                "result_kind": manifest["result_kind"],
                "packet_class": manifest["packet_class"],
                "manifest_path": detail["manifest_path"],
                "replay_package_path": detail["replay_package_path"],
            },
        }
        validate_instance(response, "export_control_plane_response.schema.json")
        return response

    if action == "handoff":
        receipt_id = query["receipt_id"]
        detail = get_export_bundle_detail(root, receipt_id, export_dir=export_dir)
        manifest = detail["manifest"]
        target_dir = root / handoff_dir
        materialized = materialize_replay_package(
            root,
            receipt_id,
            target_dir,
            export_dir=export_dir,
            extract=False,
        )
        copied_package_path = Path(materialized["copied_replay_package_path"])
        handoff_manifest = {
            "schema_version": "1.0.0",
            "handoff_id": stable_id(
                "handoff",
                {
                    "receipt_id": receipt_id,
                    "export_id": manifest["export_id"],
                    "target_dir": handoff_dir,
                },
            ),
            "receipt_id": receipt_id,
            "export_id": manifest["export_id"],
            "package_label": manifest["package_label"],
            "packet_class": manifest["packet_class"],
            "result_kind": manifest["result_kind"],
            "compatibility_posture": manifest["compatibility_posture"],
            "source_manifest_path": detail["manifest_path"],
            "source_replay_package_path": materialized["source_replay_package_path"],
            "copied_replay_package_path": materialized["copied_replay_package_path"],
            "replay_package_filename": copied_package_path.name,
            "replay_package_sha256": _sha256_file(copied_package_path),
        }
        validate_instance(handoff_manifest, "export_handoff_manifest.schema.json")
        handoff_manifest_path = target_dir / f"slice_09_handoff_manifest_{receipt_id}.json"
        handoff_manifest_path.write_text(json.dumps(handoff_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        response = {
            **_response_base(action, query),
            "handoff": {
                "receipt_id": receipt_id,
                "handoff_manifest_path": str(handoff_manifest_path),
                "copied_replay_package_path": materialized["copied_replay_package_path"],
                "replay_package_sha256": handoff_manifest["replay_package_sha256"],
            },
        }
        validate_instance(response, "export_control_plane_response.schema.json")
        return response

    raise ValueError(f"unsupported action: {action}")
