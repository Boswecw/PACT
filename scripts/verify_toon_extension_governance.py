from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.rendering.toon_registry import load_wave1_registry  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry_path = REPO_ROOT / "runtime" / "rendering" / "toon_registry.json"
    schema_path = REPO_ROOT / "99-contracts" / "schemas" / "toon_registry_wave1.schema.json"

    _assert(registry_path.exists(), "toon registry file is missing")
    _assert(schema_path.exists(), "toon registry schema is missing")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    loaded = load_wave1_registry()

    _assert(registry == loaded, "loader output must match registry payload")
    _assert(registry["supported_packet_classes"] == ["search_assist_packet"], "wave1 packet allow-list drifted")
    _assert(registry["field_order"] == ["rank", "title", "source_ref", "summary"], "wave1 field order drifted")
    _assert(registry["capability_class"] == "wave1_ranked_result_segment", "wave1 capability class drifted")
    _assert(registry["admission_stage"] == "wave1_internal", "wave1 admission stage drifted")

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_extension_governance_report.json"
    out_path.write_text(
        json.dumps(
            {
                "registry_path": str(registry_path),
                "schema_path": str(schema_path),
                "registry": registry,
                "all_green": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"report": str(out_path), "registry": registry}, indent=2))
    print("verify_toon_extension_governance: PASS")


if __name__ == "__main__":
    main()
