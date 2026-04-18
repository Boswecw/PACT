from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "toon-wave1-gate.yml"
    _assert(workflow_path.exists(), "workflow file is missing")

    text = workflow_path.read_text(encoding="utf-8")

    checks = {
        "has_checkout": "actions/checkout@v4" in text,
        "has_setup_python": "actions/setup-python@v5" in text,
        "runs_repo_gate": "python scripts/verify_toon_repo_gate.py" in text,
        "uploads_artifact": "actions/upload-artifact@v4" in text,
        "exports_toon_flag": "PACT_ENABLE_TOON_WAVE1: \"true\"" in text,
    }

    for label, ok in checks.items():
        _assert(ok, f"workflow check failed: {label}")

    out_dir = REPO_ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "toon_ci_gate_files_report.json"
    out_path.write_text(
        json.dumps(
            {
                "workflow_path": str(workflow_path),
                "workflow_sha256": _sha256(workflow_path),
                "checks": checks,
                "all_green": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"report": str(out_path), "checks": checks}, indent=2))
    print("verify_toon_ci_gate_files: PASS")


if __name__ == "__main__":
    main()
