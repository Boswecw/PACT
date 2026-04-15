from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runtime.export.operator_surface import (  # noqa: E402
    build_export_catalog,
    get_export_bundle_detail,
    materialize_replay_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="PACT Slice 08 operator-facing export surfaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="Build and print the export catalog.")
    list_parser.add_argument("--export-dir", default="harness/exports")

    show_parser = subparsers.add_parser("show", help="Show one export bundle by receipt id.")
    show_parser.add_argument("receipt_id")
    show_parser.add_argument("--export-dir", default="harness/exports")

    download_parser = subparsers.add_parser("download", help="Copy and optionally extract one replay package.")
    download_parser.add_argument("receipt_id")
    download_parser.add_argument("--export-dir", default="harness/exports")
    download_parser.add_argument("--target-dir", default="harness/downloads")
    download_parser.add_argument("--extract", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(build_export_catalog(ROOT, export_dir=args.export_dir), indent=2))
        return 0
    if args.command == "show":
        print(json.dumps(get_export_bundle_detail(ROOT, args.receipt_id, export_dir=args.export_dir), indent=2))
        return 0
    if args.command == "download":
        print(
            json.dumps(
                materialize_replay_package(
                    ROOT,
                    args.receipt_id,
                    ROOT / args.target_dir,
                    export_dir=args.export_dir,
                    extract=args.extract,
                ),
                indent=2,
            )
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
