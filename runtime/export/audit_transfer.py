from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import canonical_json, sha256_hex, stable_id

from .control_plane_surface import query_export_surface
from .operator_surface import build_export_catalog, get_export_bundle_detail


FIXED_ZIP_TIMESTAMP = (2026, 4, 15, 0, 0, 0)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_deterministic_zip(destination: Path, entries: list[tuple[str, bytes]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for archive_name, data in sorted(entries, key=lambda item: item[0]):
            info = ZipInfo(archive_name)
            info.date_time = FIXED_ZIP_TIMESTAMP
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)


def build_audit_transfer_bundle(
    root_dir: str | Path,
    request: dict[str, Any],
    *,
    export_dir: str = "harness/exports",
    handoff_dir: str = "harness/handoffs",
    audit_dir: str = "harness/audit",
    run_index_path: str | None = None,
) -> dict[str, Any]:
    root = Path(root_dir)
    receipt_ids = sorted(set(request["receipt_ids"]))
    catalog = build_export_catalog(root, export_dir=export_dir)["catalog"]
    catalog_entries = [entry for entry in catalog["entries"] if entry["receipt_id"] in set(receipt_ids)]
    catalog_entries.sort(key=lambda item: item["receipt_id"])

    filtered_catalog = {
        "schema_version": "1.0.0",
        "export_dir": export_dir,
        "bundle_count": len(catalog_entries),
        "entries": catalog_entries,
    }
    validate_instance(filtered_catalog, "export_catalog_manifest.schema.json")

    transfer_seed = {
        "receipt_ids": receipt_ids,
        "audit_dir": audit_dir,
        "run_id": request.get("run_id"),
    }
    transfer_id = stable_id("audit_transfer", transfer_seed)
    request_digest = sha256_hex(canonical_json(request))
    audit_root = root / audit_dir
    transfer_catalog_path = audit_root / f"slice_10_transfer_catalog_{transfer_id}.json"
    transfer_manifest_path = audit_root / f"slice_10_audit_transfer_manifest_{transfer_id}.json"
    transfer_bundle_path = audit_root / f"slice_10_audit_transfer_{transfer_id}.zip"

    _write_json(transfer_catalog_path, filtered_catalog)

    bundle_entries: list[tuple[str, bytes]] = [
        ("catalog/export_catalog.json", transfer_catalog_path.read_bytes()),
    ]
    included_artifacts: list[dict[str, Any]] = [
        {
            "artifact_kind": "catalog",
            "relative_path": "catalog/export_catalog.json",
            "sha256": _sha256_file(transfer_catalog_path),
        }
    ]

    if run_index_path is not None:
        run_index_file = Path(run_index_path)
        bundle_entries.append(("run_index/run_export_index.json", run_index_file.read_bytes()))
        included_artifacts.append(
            {
                "artifact_kind": "run_index",
                "relative_path": "run_index/run_export_index.json",
                "sha256": _sha256_file(run_index_file),
            }
        )

    for receipt_id in receipt_ids:
        detail = get_export_bundle_detail(root, receipt_id, export_dir=export_dir)
        handoff_response = query_export_surface(
            root,
            {"action": "handoff", "receipt_id": receipt_id},
            export_dir=export_dir,
            handoff_dir=handoff_dir,
        )
        manifest_path = Path(detail["manifest_path"])
        copied_package_path = Path(handoff_response["handoff"]["copied_replay_package_path"])
        handoff_manifest_path = Path(handoff_response["handoff"]["handoff_manifest_path"])

        manifest_archive_path = f"exports/manifests/{manifest_path.name}"
        package_archive_path = f"handoffs/packages/{copied_package_path.name}"
        handoff_archive_path = f"handoffs/manifests/{handoff_manifest_path.name}"

        bundle_entries.extend(
            [
                (manifest_archive_path, manifest_path.read_bytes()),
                (package_archive_path, copied_package_path.read_bytes()),
                (handoff_archive_path, handoff_manifest_path.read_bytes()),
            ]
        )
        included_artifacts.extend(
            [
                {
                    "artifact_kind": "export_manifest",
                    "relative_path": manifest_archive_path,
                    "sha256": _sha256_file(manifest_path),
                },
                {
                    "artifact_kind": "replay_package",
                    "relative_path": package_archive_path,
                    "sha256": _sha256_file(copied_package_path),
                },
                {
                    "artifact_kind": "handoff_manifest",
                    "relative_path": handoff_archive_path,
                    "sha256": _sha256_file(handoff_manifest_path),
                },
            ]
        )

    transfer_manifest = {
        "schema_version": "1.0.0",
        "transfer_id": transfer_id,
        "request_digest": request_digest,
        "receipt_ids": receipt_ids,
        "artifact_count": len(included_artifacts),
        "transfer_bundle_filename": transfer_bundle_path.name,
        "transfer_catalog_filename": transfer_catalog_path.name,
        "included_artifacts": included_artifacts,
    }
    if request.get("run_id"):
        transfer_manifest["run_id"] = request["run_id"]
    if run_index_path is not None:
        transfer_manifest["source_run_index_filename"] = Path(run_index_path).name

    validate_instance(transfer_manifest, "audit_transfer_manifest.schema.json")
    _write_json(transfer_manifest_path, transfer_manifest)

    bundle_entries.append(("transfer/audit_transfer_manifest.json", transfer_manifest_path.read_bytes()))
    _write_deterministic_zip(transfer_bundle_path, bundle_entries)

    return {
        "transfer_manifest": transfer_manifest,
        "transfer_manifest_path": str(transfer_manifest_path),
        "transfer_bundle_path": str(transfer_bundle_path),
        "transfer_catalog_path": str(transfer_catalog_path),
    }
