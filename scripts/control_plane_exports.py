from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runtime.export.control_plane_surface import query_export_surface  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="PACT Slice 09 control-plane export queries.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog", help="Run a stable catalog query.")
    catalog_parser.add_argument("--receipt-ids", default="")
    catalog_parser.add_argument("--packet-class")
    catalog_parser.add_argument("--result-kind")
    catalog_parser.add_argument("--package-label")

    detail_parser = subparsers.add_parser("detail", help="Run a stable detail query.")
    detail_parser.add_argument("receipt_id")

    handoff_parser = subparsers.add_parser("handoff", help="Create a hardened handoff package.")
    handoff_parser.add_argument("receipt_id")
    handoff_parser.add_argument("--handoff-dir", default="harness/handoffs")

    args = parser.parse_args()

    if args.command == "catalog":
        query = {
            "action": "catalog",
            "receipt_ids": [item for item in args.receipt_ids.split(",") if item],
            "packet_class": args.packet_class,
            "result_kind": args.result_kind,
            "package_label": args.package_label,
        }
        print(json.dumps(query_export_surface(ROOT, query), indent=2))
        return 0

    if args.command == "detail":
        print(json.dumps(query_export_surface(ROOT, {"action": "detail", "receipt_id": args.receipt_id}), indent=2))
        return 0

    if args.command == "handoff":
        print(
            json.dumps(
                query_export_surface(
                    ROOT,
                    {"action": "handoff", "receipt_id": args.receipt_id},
                    handoff_dir=args.handoff_dir,
                ),
                indent=2,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
