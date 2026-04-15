from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from runtime.validation.schema_validator import validate_instance


def _json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_paths(export_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in export_dir.glob("slice_07_export_manifest_*.json")
        if path.is_file() and path.name != "slice_08_export_catalog.json"
    )


def _catalog_entry(manifest_path: Path, manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    replay_zip = export_dir = manifest_path.parent / manifest["replay_package_filename"]
    return {
        "export_id": manifest["export_id"],
        "receipt_id": manifest["receipt_id"],
        "request_id": manifest["request_id"],
        "trace_id": manifest["trace_id"],
        "packet_class": manifest["packet_class"],
        "result_kind": manifest["result_kind"],
        "execution_mode": manifest["execution_mode"],
        "package_label": manifest["package_label"],
        "compatibility_posture": manifest["compatibility_posture"],
        "manifest_filename": manifest_path.name,
        "replay_package_filename": manifest["replay_package_filename"],
        "manifest_path": str(manifest_path.relative_to(root)),
        "replay_package_path": str(replay_zip.relative_to(root)),
    }


def build_export_catalog(root_dir: str | Path, export_dir: str = "harness/exports") -> dict[str, Any]:
    root = Path(root_dir)
    export_root = root / export_dir
    export_root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for manifest_path in _manifest_paths(export_root):
        manifest = _json_load(manifest_path)
        validate_instance(manifest, "export_bundle_manifest.schema.json")
        entries.append(_catalog_entry(manifest_path, manifest, root))

    entries.sort(key=lambda item: (item["receipt_id"], item["manifest_filename"]))
    catalog = {
        "schema_version": "1.0.0",
        "export_dir": export_dir,
        "bundle_count": len(entries),
        "entries": entries,
    }
    validate_instance(catalog, "export_catalog_manifest.schema.json")

    catalog_path = export_root / "slice_08_export_catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "catalog": catalog,
        "catalog_path": str(catalog_path),
    }


def get_export_bundle_detail(root_dir: str | Path, receipt_id: str, export_dir: str = "harness/exports") -> dict[str, Any]:
    root = Path(root_dir)
    export_root = root / export_dir
    manifest_path = export_root / f"slice_07_export_manifest_{receipt_id}.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"export manifest not found for receipt_id={receipt_id}")

    manifest = _json_load(manifest_path)
    validate_instance(manifest, "export_bundle_manifest.schema.json")
    replay_package_path = export_root / manifest["replay_package_filename"]
    if not replay_package_path.exists():
        raise FileNotFoundError(f"replay package missing for receipt_id={receipt_id}")

    return {
        "receipt_id": receipt_id,
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "replay_package_path": str(replay_package_path),
    }


def materialize_replay_package(
    root_dir: str | Path,
    receipt_id: str,
    target_dir: str | Path,
    *,
    export_dir: str = "harness/exports",
    extract: bool = False,
) -> dict[str, Any]:
    detail = get_export_bundle_detail(root_dir, receipt_id, export_dir=export_dir)
    target_root = Path(target_dir)
    target_root.mkdir(parents=True, exist_ok=True)

    source_zip = Path(detail["replay_package_path"])
    copied_zip = target_root / source_zip.name
    copied_zip.write_bytes(source_zip.read_bytes())

    extracted_dir = None
    extracted_members: list[str] = []
    if extract:
        extracted_dir = target_root / receipt_id
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(copied_zip) as archive:
            archive.extractall(extracted_dir)
            extracted_members = sorted(archive.namelist())

    return {
        "receipt_id": receipt_id,
        "source_replay_package_path": str(source_zip),
        "copied_replay_package_path": str(copied_zip),
        "extracted_dir": str(extracted_dir) if extracted_dir else None,
        "extracted_members": extracted_members,
    }
