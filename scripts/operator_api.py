from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runtime.export.operator_api import handle_operator_request  # noqa: E402


def _compact(value: dict) -> dict:
    return {
        key: item
        for key, item in value.items()
        if item is not None and item != [] and item != ""
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PACT Slice 11 operator API boundary.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog")
    catalog_parser.add_argument("--receipt-ids", default="")
    catalog_parser.add_argument("--package-label")
    catalog_parser.add_argument("--packet-class")
    catalog_parser.add_argument("--result-kind")

    detail_parser = subparsers.add_parser("detail")
    detail_parser.add_argument("receipt_id")

    handoff_parser = subparsers.add_parser("handoff")
    handoff_parser.add_argument("receipt_id")
    handoff_parser.add_argument("--handoff-dir", default="harness/handoffs")

    audit_parser = subparsers.add_parser("audit-transfer")
    audit_parser.add_argument("--receipt-ids", required=True)
    audit_parser.add_argument("--handoff-dir", default="harness/handoffs")
    audit_parser.add_argument("--audit-dir", default="harness/audit")

    run_index_parser = subparsers.add_parser("run-index")
    run_index_parser.add_argument("--audit-dir", default="harness/audit")

    run_audit_parser = subparsers.add_parser("run-audit-transfer")
    run_audit_parser.add_argument("run_id")
    run_audit_parser.add_argument("--handoff-dir", default="harness/handoffs")
    run_audit_parser.add_argument("--audit-dir", default="harness/audit")

    args = parser.parse_args()

    if args.command == "catalog":
        request = _compact(
            {
                "schema_version": "1.0.0",
                "action": "catalog",
                "receipt_ids": [item for item in args.receipt_ids.split(",") if item],
                "package_label": args.package_label,
                "packet_class": args.packet_class,
                "result_kind": args.result_kind,
            }
        )
    elif args.command == "detail":
        request = {
            "schema_version": "1.0.0",
            "action": "detail",
            "receipt_id": args.receipt_id,
        }
    elif args.command == "handoff":
        request = {
            "schema_version": "1.0.0",
            "action": "handoff",
            "receipt_id": args.receipt_id,
            "handoff_dir": args.handoff_dir,
        }
    elif args.command == "audit-transfer":
        request = {
            "schema_version": "1.0.0",
            "action": "audit_transfer",
            "receipt_ids": [item for item in args.receipt_ids.split(",") if item],
            "handoff_dir": args.handoff_dir,
            "audit_dir": args.audit_dir,
        }
    elif args.command == "run-index":
        request = {
            "schema_version": "1.0.0",
            "action": "run_index",
            "audit_dir": args.audit_dir,
        }
    elif args.command == "run-audit-transfer":
        request = {
            "schema_version": "1.0.0",
            "action": "run_audit_transfer",
            "run_id": args.run_id,
            "handoff_dir": args.handoff_dir,
            "audit_dir": args.audit_dir,
        }
    else:
        return 1

    print(json.dumps(handle_operator_request(ROOT, request), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
