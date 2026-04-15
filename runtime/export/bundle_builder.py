from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import canonical_json, sha256_hex, stable_id

_FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)


def _stable_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _zip_info(name: str) -> ZipInfo:
    info = ZipInfo(filename=name, date_time=_FIXED_ZIP_DT)
    info.compress_type = ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o644 << 16
    return info


def _copy_request_for_replay(request: dict[str, Any]) -> dict[str, Any]:
    replay_request = json.loads(canonical_json(request))
    replay_request.pop("emit_control_plane_export", None)
    replay_request.pop("export_dir", None)
    replay_request.pop("package_label", None)
    replay_request.pop("control_plane_export", None)
    return replay_request


def _relativize(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _member(logical_name: str, archive_path: str, payload: bytes, *, source_path: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "logical_name": logical_name,
        "archive_path": archive_path,
        "sha256": _sha256_bytes(payload),
        "payload": payload,
    }
    if source_path:
        record["source_path"] = source_path
    return record


def build_export_bundle(
    root_dir: str | Path,
    *,
    request: dict[str, Any],
    result: dict[str, Any],
    export_dir: str = "harness/exports",
    package_label: str = "operator_replay",
) -> dict[str, str]:
    root = Path(root_dir)
    out_dir = root / export_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = result["packet"]
    receipt = result["receipt"]
    replay_request = _copy_request_for_replay(request)
    result_kind = "success" if result.get("ok") else "safe_failure"
    execution_mode = request.get("execution_mode", "replay")
    receipt_id = receipt["receipt_id"]

    export_id = stable_id(
        "exp",
        {
            "package_label": package_label,
            "request_id": receipt["request_id"],
            "receipt_id": receipt_id,
            "result_kind": result_kind,
        },
    )

    replay_package_filename = f"slice_07_replay_package_{receipt_id}.zip"
    manifest_filename = f"slice_07_export_manifest_{receipt_id}.json"
    replay_package_path = out_dir / replay_package_filename
    export_manifest_path = out_dir / manifest_filename

    members: list[dict[str, Any]] = [
        _member("replay_request", "replay/request.json", _stable_json_bytes(replay_request)),
        _member("packet", "observed/packet.json", _stable_json_bytes(packet)),
        _member("receipt", "observed/receipt.json", _stable_json_bytes(receipt)),
    ]

    optional_sources = [
        ("telemetry_report", "telemetry/runtime_report.json", result.get("telemetry_path")),
        ("telemetry_manifest", "telemetry/runtime_manifest.json", result.get("manifest_path")),
        ("evidence_bundle", "evidence/evidence_bundle.json", result.get("evidence_path")),
    ]
    for logical_name, archive_path, source in optional_sources:
        if not source:
            continue
        source_path = Path(source)
        if not source_path.exists():
            continue
        members.append(
            _member(
                logical_name,
                archive_path,
                source_path.read_bytes(),
                source_path=_relativize(source_path, root),
            )
        )

    members.sort(key=lambda item: item["archive_path"])
    manifest = {
        "schema_version": "1.0.0",
        "export_id": export_id,
        "package_label": package_label,
        "result_kind": result_kind,
        "request_id": receipt["request_id"],
        "trace_id": receipt["trace_id"],
        "receipt_id": receipt_id,
        "packet_id": receipt["packet_id"],
        "packet_class": receipt["packet_class"],
        "execution_mode": execution_mode,
        "replay_package_filename": replay_package_filename,
        "manifest_filename": manifest_filename,
        "replay_request_archive_path": "replay/request.json",
        "version_set": receipt["version_set"],
        "source_lineage_digest": receipt["source_lineage_digest"],
        "compatibility_posture": receipt["version_set"].get("compatibility_posture", "compatible"),
        "included_artifacts": [
            {
                key: value
                for key, value in item.items()
                if key in {"logical_name", "archive_path", "sha256", "source_path"}
            }
            for item in members
        ],
    }
    validate_instance(manifest, "export_bundle_manifest.schema.json")
    manifest_bytes = _stable_json_bytes(manifest)

    export_manifest_path.write_bytes(manifest_bytes)

    with ZipFile(replay_package_path, mode="w") as archive:
        for item in members:
            archive.writestr(_zip_info(item["archive_path"]), item["payload"])
        archive.writestr(_zip_info("manifest/export_bundle_manifest.json"), manifest_bytes)

    return {
        "export_manifest_path": str(export_manifest_path),
        "replay_package_path": str(replay_package_path),
        "export_id": export_id,
    }
