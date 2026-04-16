from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import canonical_json, sha256_hex, stable_id

from .audit_transfer import FIXED_ZIP_TIMESTAMP, build_audit_transfer_bundle
from .operator_surface import get_export_bundle_detail
from .run_index import build_run_export_index, resolve_run_receipts

PACKET_CLASS_ORDER = [
    "answer_packet",
    "policy_response_packet",
    "search_assist_packet",
]
RESULT_KIND_ORDER = ["success", "safe_failure"]
EXECUTION_MODE_ORDER = ["live", "replay"]
DEGRADATION_STATE_ORDER = [
    "normal",
    "retrieval_degraded",
    "rerank_degraded",
    "pruning_degraded",
    "cache_degraded",
    "minimum_viable_packet",
    "safe_failure",
]
COMPATIBILITY_POSTURE_ORDER = ["compatible", "migration_required", "incompatible"]
MODEL_CALL_ALLOWED_ORDER = ["allowed", "blocked"]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_deterministic_zip(destination: Path, entries: list[tuple[str, bytes]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for archive_name, data in sorted(entries, key=lambda item: item[0]):
            info = ZipInfo(archive_name)
            info.date_time = FIXED_ZIP_TIMESTAMP
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _aggregate_compatibility_posture(counts: dict[str, int]) -> str:
    if counts["incompatible"] > 0:
        return "incompatible"
    if counts["migration_required"] > 0:
        return "migration_required"
    return "compatible"


def _extract_receipt(detail: dict[str, Any]) -> dict[str, Any]:
    manifest = detail["manifest"]
    receipt_entry = next(
        artifact
        for artifact in manifest["included_artifacts"]
        if artifact["logical_name"] == "receipt"
    )
    replay_package_path = Path(detail["replay_package_path"])
    with ZipFile(replay_package_path) as archive:
        receipt = json.loads(archive.read(receipt_entry["archive_path"]).decode("utf-8"))
    validate_instance(receipt, "runtime_receipt.schema.json")
    return receipt


def _init_counts() -> dict[str, dict[str, int]]:
    return {
        "packet_class_counts": {key: 0 for key in PACKET_CLASS_ORDER},
        "result_kind_counts": {key: 0 for key in RESULT_KIND_ORDER},
        "execution_mode_counts": {key: 0 for key in EXECUTION_MODE_ORDER},
        "degradation_state_counts": {key: 0 for key in DEGRADATION_STATE_ORDER},
        "compatibility_posture_counts": {key: 0 for key in COMPATIBILITY_POSTURE_ORDER},
        "model_call_allowed_counts": {key: 0 for key in MODEL_CALL_ALLOWED_ORDER},
    }


def _render_count_block(title: str, order: list[str], counts: dict[str, int]) -> list[str]:
    lines = [f"## {title}"]
    for key in order:
        lines.append(f"- {key}: {counts[key]}")
    lines.append("")
    return lines


def build_run_export_summary_package(
    root_dir: str | Path,
    request: dict[str, Any],
    *,
    export_dir: str = "harness/exports",
    handoff_dir: str = "harness/handoffs",
    audit_dir: str = "harness/audit",
) -> dict[str, Any]:
    validate_instance(request, "operator_api_request.schema.json")
    if request["action"] != "run_export_summary_package":
        raise ValueError("build_run_export_summary_package requires action=run_export_summary_package")

    root = Path(root_dir)
    request_digest = sha256_hex(canonical_json(request))

    run_index = build_run_export_index(
        root,
        export_dir=export_dir,
        output_path=f"{audit_dir}/slice_11_run_export_index.json",
    )
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

    audit_root = root / request.get("audit_dir", audit_dir)
    bundle_root = audit_root / "runs" / request["run_id"]
    bundle_root.mkdir(parents=True, exist_ok=True)

    export_package_id = stable_id(
        "run_export_summary",
        {
            "run_id": request["run_id"],
            "receipt_ids": receipt_ids,
            "request_digest": request_digest,
        },
    )
    summary_path = bundle_root / f"slice_12_audit_summary_{export_package_id}.md"
    registry_record_path = bundle_root / f"slice_12_export_registry_record_{export_package_id}.json"
    summary_manifest_path = bundle_root / f"slice_12_run_export_summary_package_manifest_{export_package_id}.json"
    summary_package_path = bundle_root / f"slice_12_run_export_summary_package_{export_package_id}.zip"

    counts = _init_counts()
    safe_failure_invoked_count = 0
    source_scopes: set[str] = set()
    receipt_rows: list[dict[str, str]] = []

    for receipt_id in receipt_ids:
        detail = get_export_bundle_detail(root, receipt_id, export_dir=export_dir)
        manifest = detail["manifest"]
        receipt = _extract_receipt(detail)

        counts["packet_class_counts"][manifest["packet_class"]] += 1
        counts["result_kind_counts"][manifest["result_kind"]] += 1
        counts["execution_mode_counts"][manifest["execution_mode"]] += 1
        counts["compatibility_posture_counts"][manifest["compatibility_posture"]] += 1
        counts["degradation_state_counts"][receipt["degradation_state"]] += 1
        counts["model_call_allowed_counts"]["allowed" if receipt["model_call_allowed"] else "blocked"] += 1
        safe_failure_invoked_count += 1 if receipt["safe_failure_invoked"] else 0
        source_scopes.add(receipt["source_lineage_digest"]["source_scope"])
        receipt_rows.append(
            {
                "receipt_id": receipt_id,
                "packet_class": manifest["packet_class"],
                "result_kind": manifest["result_kind"],
                "execution_mode": manifest["execution_mode"],
                "compatibility_posture": manifest["compatibility_posture"],
                "degradation_state": receipt["degradation_state"],
                "model_call_allowed": "true" if receipt["model_call_allowed"] else "false",
                "safe_failure_invoked": "true" if receipt["safe_failure_invoked"] else "false",
            }
        )

    receipt_rows.sort(key=lambda item: item["receipt_id"])
    included_paths = [
        "transfer/run_audit_transfer_bundle.zip",
        "transfer/audit_transfer_manifest.json",
        "summary/audit_summary.md",
        "registry/export_registry_record.json",
    ]
    compatibility_posture = _aggregate_compatibility_posture(counts["compatibility_posture_counts"])

    summary_lines = [
        "# PACT Run Export Summary Package",
        "",
        f"- export_package_id: `{export_package_id}`",
        f"- run_id: `{request['run_id']}`",
        f"- transfer_id: `{transfer['transfer_manifest']['transfer_id']}`",
        f"- receipt_count: `{len(receipt_ids)}`",
        f"- transfer_artifact_count: `{transfer['transfer_manifest']['artifact_count']}`",
        f"- package_artifact_count: `{len(included_paths)}`",
        f"- compatibility_posture: `{compatibility_posture}`",
        f"- source_run_index_path: `{_relative(root, Path(run_index['index_path']))}`",
        f"- source_transfer_manifest_path: `{_relative(root, Path(transfer['transfer_manifest_path']))}`",
        f"- source_transfer_bundle_path: `{_relative(root, Path(transfer['transfer_bundle_path']))}`",
        "",
    ]
    summary_lines.extend(_render_count_block("Packet Class Counts", PACKET_CLASS_ORDER, counts["packet_class_counts"]))
    summary_lines.extend(_render_count_block("Result Kind Counts", RESULT_KIND_ORDER, counts["result_kind_counts"]))
    summary_lines.extend(_render_count_block("Execution Mode Counts", EXECUTION_MODE_ORDER, counts["execution_mode_counts"]))
    summary_lines.extend(_render_count_block("Degradation State Counts", DEGRADATION_STATE_ORDER, counts["degradation_state_counts"]))
    summary_lines.extend(_render_count_block("Model Call Allowed Counts", MODEL_CALL_ALLOWED_ORDER, counts["model_call_allowed_counts"]))
    summary_lines.extend(
        _render_count_block(
            "Compatibility Posture Counts",
            COMPATIBILITY_POSTURE_ORDER,
            counts["compatibility_posture_counts"],
        )
    )
    summary_lines.extend(
        [
            "## Safe Failure Invocation",
            f"- safe_failure_invoked_count: {safe_failure_invoked_count}",
            "",
            "## Source Scopes",
        ]
    )
    for scope in sorted(source_scopes):
        summary_lines.append(f"- {scope}")
    summary_lines.append("")
    summary_lines.append("## Included Package Paths")
    for path in included_paths:
        summary_lines.append(f"- {path}")
    summary_lines.append("")
    summary_lines.extend(
        [
            "## Compatibility Note",
            "- run_audit_transfer remains the nested governed bundle source for this package.",
            "- manual receipt-list audit transfer remains available as a separate compatibility path.",
            "",
            "## Receipt Detail",
            "- receipt_id | packet_class | result_kind | execution_mode | compatibility_posture | degradation_state | model_call_allowed | safe_failure_invoked",
        ]
    )
    for row in receipt_rows:
        summary_lines.append(
            "- "
            + " | ".join(
                [
                    row["receipt_id"],
                    row["packet_class"],
                    row["result_kind"],
                    row["execution_mode"],
                    row["compatibility_posture"],
                    row["degradation_state"],
                    row["model_call_allowed"],
                    row["safe_failure_invoked"],
                ]
            )
        )
    summary_lines.append("")
    summary_body = "\n".join(summary_lines)
    _write_text(summary_path, summary_body)

    registry_record = {
        "schema_version": "1.0.0",
        "record_type": "run_export_summary_package",
        "export_package_id": export_package_id,
        "run_id": request["run_id"],
        "transfer_id": transfer["transfer_manifest"]["transfer_id"],
        "request_digest": request_digest,
        "compatibility_posture": compatibility_posture,
        "source_run_index_path": _relative(root, Path(run_index["index_path"])),
        "source_transfer_bundle_path": _relative(root, Path(transfer["transfer_bundle_path"])),
        "source_transfer_manifest_path": _relative(root, Path(transfer["transfer_manifest_path"])),
        "bundle_root": _relative(root, bundle_root),
        "summary_path": _relative(root, summary_path),
        "summary_manifest_path": _relative(root, summary_manifest_path),
        "summary_package_path": _relative(root, summary_package_path),
        "receipt_count": len(receipt_ids),
        "transfer_artifact_count": transfer["transfer_manifest"]["artifact_count"],
        "package_artifact_count": len(included_paths),
        "receipt_ids": receipt_ids,
        "source_scopes": sorted(source_scopes),
        "packet_class_counts": counts["packet_class_counts"],
        "result_kind_counts": counts["result_kind_counts"],
        "execution_mode_counts": counts["execution_mode_counts"],
        "degradation_state_counts": counts["degradation_state_counts"],
        "model_call_allowed_counts": counts["model_call_allowed_counts"],
        "safe_failure_invoked_count": safe_failure_invoked_count,
        "compatibility_posture_counts": counts["compatibility_posture_counts"],
        "included_paths": included_paths,
    }
    validate_instance(registry_record, "run_export_summary_registry_record.schema.json")
    _write_json(registry_record_path, registry_record)

    summary_manifest = {
        "schema_version": "1.0.0",
        "export_package_id": export_package_id,
        "run_id": request["run_id"],
        "transfer_id": transfer["transfer_manifest"]["transfer_id"],
        "request_digest": request_digest,
        "bundle_root": _relative(root, bundle_root),
        "source_run_index_path": _relative(root, Path(run_index["index_path"])),
        "source_transfer_bundle_path": _relative(root, Path(transfer["transfer_bundle_path"])),
        "source_transfer_manifest_path": _relative(root, Path(transfer["transfer_manifest_path"])),
        "summary_path": _relative(root, summary_path),
        "registry_record_path": _relative(root, registry_record_path),
        "summary_manifest_path": _relative(root, summary_manifest_path),
        "summary_package_path": _relative(root, summary_package_path),
        "receipt_ids": receipt_ids,
        "artifact_count": len(included_paths),
        "included_artifacts": [
            {
                "artifact_kind": "audit_transfer_bundle",
                "relative_path": "transfer/run_audit_transfer_bundle.zip",
                "sha256": _sha256_file(Path(transfer["transfer_bundle_path"])),
            },
            {
                "artifact_kind": "audit_transfer_manifest",
                "relative_path": "transfer/audit_transfer_manifest.json",
                "sha256": _sha256_file(Path(transfer["transfer_manifest_path"])),
            },
            {
                "artifact_kind": "audit_summary",
                "relative_path": "summary/audit_summary.md",
                "sha256": _sha256_file(summary_path),
            },
            {
                "artifact_kind": "registry_record",
                "relative_path": "registry/export_registry_record.json",
                "sha256": _sha256_file(registry_record_path),
            },
        ],
    }
    validate_instance(summary_manifest, "run_export_summary_package_manifest.schema.json")
    _write_json(summary_manifest_path, summary_manifest)

    bundle_entries = [
        ("transfer/run_audit_transfer_bundle.zip", Path(transfer["transfer_bundle_path"]).read_bytes()),
        ("transfer/audit_transfer_manifest.json", Path(transfer["transfer_manifest_path"]).read_bytes()),
        ("summary/audit_summary.md", summary_path.read_bytes()),
        ("registry/export_registry_record.json", registry_record_path.read_bytes()),
        ("summary/run_export_summary_package_manifest.json", summary_manifest_path.read_bytes()),
    ]
    _write_deterministic_zip(summary_package_path, bundle_entries)

    return {
        "summary_manifest": summary_manifest,
        "summary_manifest_path": str(summary_manifest_path),
        "summary_package_path": str(summary_package_path),
        "summary_path": str(summary_path),
        "registry_record": registry_record,
        "registry_record_path": str(registry_record_path),
        "package_root": str(bundle_root),
    }
