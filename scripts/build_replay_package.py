from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Slice 07 and emit an operator replay package.")
    parser.add_argument("request_json", help="Path to a JSON file containing a PACT request payload.")
    parser.add_argument("--export-dir", default="harness/exports", help="Relative export directory under the repo root.")
    parser.add_argument("--package-label", default="operator_replay", help="Package label to stamp into the export manifest.")
    args = parser.parse_args()

    request_path = (ROOT / args.request_json).resolve() if not Path(args.request_json).is_absolute() else Path(args.request_json)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["emit_control_plane_export"] = True
    request["control_plane_export"] = {
        "export_dir": args.export_dir,
        "package_label": args.package_label,
    }

    sys.path.insert(0, str(ROOT))
    from runtime.engine import execute_slice_07  # noqa: WPS433

    result = execute_slice_07(request)
    output = {
        "ok": result["ok"],
        "packet_class": result["packet"]["packet_class"],
        "receipt_id": result["receipt"]["receipt_id"],
        "export_manifest_path": result.get("export_manifest_path"),
        "replay_package_path": result.get("replay_package_path"),
        "control_plane_export_ok": result.get("control_plane_export_ok", False),
    }
    print(json.dumps(output, indent=2))
    return 0 if result.get("control_plane_export_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
