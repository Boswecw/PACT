from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.validation.schema_validator import validate_instance
from src.shared.pact_utils import stable_id

from .operator_surface import get_export_bundle_detail


def build_run_export_index(
    root_dir: str | Path,
    *,
    report_path: str = "harness/regression/slice_07_verification_report.json",
    export_dir: str = "harness/exports",
    output_path: str = "harness/audit/slice_11_run_export_index.json",
) -> dict[str, Any]:
    root = Path(root_dir)
    report_file = root / report_path
    report = json.loads(report_file.read_text(encoding="utf-8"))

    receipt_ids = sorted({item["receipt_id"] for item in report["results"]})
    case_ids = sorted(item["case_id"] for item in report["results"])

    packet_classes = set()
    result_kinds = set()
    for receipt_id in receipt_ids:
        detail = get_export_bundle_detail(root, receipt_id, export_dir=export_dir)
        manifest = detail["manifest"]
        packet_classes.add(manifest["packet_class"])
        result_kinds.add(manifest["result_kind"])

    run_id = stable_id(
        "run_set",
        {
            "report_path": report_path,
            "receipt_ids": receipt_ids,
            "case_ids": case_ids,
        },
    )
    index = {
        "schema_version": "1.0.0",
        "generated_from_report": report_path,
        "run_count": 1,
        "runs": [
            {
                "run_id": run_id,
                "source_report_path": report_path,
                "receipt_count": len(receipt_ids),
                "receipt_ids": receipt_ids,
                "case_ids": case_ids,
                "packet_classes": sorted(packet_classes),
                "result_kinds": sorted(result_kinds),
                "export_manifest_count": len(receipt_ids),
            }
        ],
    }
    validate_instance(index, "run_export_index.schema.json")
    destination = root / output_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "index": index,
        "index_path": str(destination),
    }


def resolve_run_receipts(index: dict[str, Any], run_id: str) -> list[str]:
    for run in index["runs"]:
        if run["run_id"] == run_id:
            return list(run["receipt_ids"])
    raise KeyError(f"unknown run_id: {run_id}")
