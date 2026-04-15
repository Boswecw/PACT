from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import canonical_json, sha256_hex

from .audit_transfer import build_audit_transfer_bundle
from .control_plane_surface import query_export_surface
from .run_index import build_run_export_index, resolve_run_receipts



def _response_base(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "action": request["action"],
        "ok": True,
        "request_digest": sha256_hex(canonical_json(request)),
    }


def handle_operator_request(
    root_dir: str | Path,
    request: dict[str, Any],
    *,
    export_dir: str = "harness/exports",
    handoff_dir: str = "harness/handoffs",
    audit_dir: str = "harness/audit",
) -> dict[str, Any]:
    validate_instance(request, "operator_api_request.schema.json")
    root = Path(root_dir)
    action = request["action"]

    if action in {"catalog", "detail", "handoff"}:
        response = query_export_surface(
            root,
            request,
            export_dir=export_dir,
            handoff_dir=request.get("handoff_dir", handoff_dir),
        )
        normalized = {**_response_base(request)}
        if action == "catalog":
            normalized["result_count"] = response["result_count"]
            normalized["results"] = response["results"]
        elif action == "detail":
            normalized["detail"] = response["detail"]
        elif action == "handoff":
            normalized["handoff"] = response["handoff"]
        validate_instance(normalized, "operator_api_response.schema.json")
        return normalized

    if action == "run_index":
        run_index = build_run_export_index(root, export_dir=export_dir, output_path=f"{audit_dir}/slice_11_run_export_index.json")
        normalized = {
            **_response_base(request),
            "run_index": {
                "index_path": run_index["index_path"],
                "run_count": run_index["index"]["run_count"],
                "runs": run_index["index"]["runs"],
            },
        }
        validate_instance(normalized, "operator_api_response.schema.json")
        return normalized

    if action == "audit_transfer":
        transfer = build_audit_transfer_bundle(
            root,
            request,
            export_dir=export_dir,
            handoff_dir=request.get("handoff_dir", handoff_dir),
            audit_dir=request.get("audit_dir", audit_dir),
        )
        normalized = {
            **_response_base(request),
            "audit_transfer": {
                "transfer_id": transfer["transfer_manifest"]["transfer_id"],
                "transfer_manifest_path": transfer["transfer_manifest_path"],
                "transfer_bundle_path": transfer["transfer_bundle_path"],
                "artifact_count": transfer["transfer_manifest"]["artifact_count"],
                "receipt_ids": transfer["transfer_manifest"]["receipt_ids"],
            },
        }
        validate_instance(normalized, "operator_api_response.schema.json")
        return normalized

    if action == "run_audit_transfer":
        run_index = build_run_export_index(root, export_dir=export_dir, output_path=f"{audit_dir}/slice_11_run_export_index.json")
        receipt_ids = resolve_run_receipts(run_index["index"], request["run_id"])
        transfer_request = {
            **request,
            "receipt_ids": receipt_ids,
        }
        transfer = build_audit_transfer_bundle(
            root,
            transfer_request,
            export_dir=export_dir,
            handoff_dir=request.get("handoff_dir", handoff_dir),
            audit_dir=request.get("audit_dir", audit_dir),
            run_index_path=run_index["index_path"],
        )
        normalized = {
            **_response_base(request),
            "audit_transfer": {
                "transfer_id": transfer["transfer_manifest"]["transfer_id"],
                "transfer_manifest_path": transfer["transfer_manifest_path"],
                "transfer_bundle_path": transfer["transfer_bundle_path"],
                "artifact_count": transfer["transfer_manifest"]["artifact_count"],
                "receipt_ids": transfer["transfer_manifest"]["receipt_ids"],
                "run_id": request["run_id"],
            },
        }
        validate_instance(normalized, "operator_api_response.schema.json")
        return normalized

    raise ValueError(f"unsupported action: {action}")
