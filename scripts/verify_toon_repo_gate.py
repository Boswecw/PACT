from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"

SCRIPTS = [
    ("slice_01_boundary", "scripts/verify_toon_slice_01.py"),
    ("slice_02_wave1", "scripts/verify_toon_wave1.py"),
    ("slice_03_observability", "scripts/verify_toon_observability.py"),
]

REPO_MAP_TARGETS = [
    "runtime/rendering/__init__.py",
    "runtime/rendering/renderer.py",
    "runtime/rendering/toon_registry.json",
    "runtime/rendering/toon_registry.py",
    "runtime/observability/__init__.py",
    "runtime/observability/toon_evidence.py",
    "runtime/engine.py",
    "scripts/verify_toon_slice_01.py",
    "scripts/verify_toon_wave1.py",
    "scripts/verify_toon_observability.py",
    "scripts/verify_toon_repo_gate.py",
    "99-contracts/schemas/serialization_evidence.schema.json",
    "99-contracts/schemas/serialization_evidence_segment_meta.schema.json",
    "99-contracts/schemas/serialization_evidence_token_estimates.schema.json",
    "99-contracts/schemas/runtime_receipt.schema.json",
    "99-contracts/schemas/safe_failure_packet.schema.json",
    "doc/system/10_service-contract/01_receipt_serialization_evidence_strategy.md",
    "doc/system/20_runtime/01_runtime_serialization_boundary.md",
    "doc/system/40_governance/01_toon_wave1_rollout_and_feature_flag.md",
    "doc/system/50_operations/01_toon_wave1_proof_gate.md",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_script(label: str, rel_path: str) -> dict:
    env = os.environ.copy()
    env["PACT_ENABLE_TOON_WAVE1"] = "true"
    proc = subprocess.run(
        [sys.executable, rel_path],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
    )
    return {
        "label": label,
        "script": rel_path,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def build_repo_map() -> dict:
    entries = []
    for rel in REPO_MAP_TARGETS:
        path = REPO_ROOT / rel
        entries.append(
            {
                "path": rel,
                "exists": path.exists(),
                "kind": "dir" if path.is_dir() else "file" if path.exists() else "missing",
            }
        )
    return {"entries": entries}


def write_repo_map(repo_map: dict) -> Path:
    DOCS_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_EVIDENCE_DIR / "toon_wave1_repo_map.md"

    lines = [
        "# TOON Wave 1 Repo Map",
        "",
        "| Path | Exists | Kind |",
        "|---|---:|---|",
    ]
    for entry in repo_map["entries"]:
        lines.append(f"| `{entry['path']}` | {'yes' if entry['exists'] else 'no'} | {entry['kind']} |")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    runs = [run_script(label, script) for label, script in SCRIPTS]

    for run in runs:
        _assert(run["ok"], f"gate failed: {run['label']}\nSTDOUT:\n{run['stdout']}\nSTDERR:\n{run['stderr']}")

    repo_map = build_repo_map()
    _assert(all(entry["exists"] for entry in repo_map["entries"]), "repo map contains missing expected files")

    repo_map_path = write_repo_map(repo_map)

    artifacts = {
        "slice_02_operator_examples": str(REPO_ROOT / "docs" / "evidence" / "toon_wave1_operator_examples.md"),
        "slice_03_observability_report": str(REPO_ROOT / "docs" / "evidence" / "toon_observability_report.json"),
        "slice_03_observability_stream": str(REPO_ROOT / ".pact_local" / "toon_events.jsonl"),
        "slice_04_repo_map": str(repo_map_path),
    }

    for label, artifact in artifacts.items():
        _assert(Path(artifact).exists(), f"missing artifact: {label} -> {artifact}")

    report = {
        "repo_gate": "toon_wave1",
        "all_green": True,
        "runs": [
            {
                "label": run["label"],
                "script": run["script"],
                "returncode": run["returncode"],
                "ok": run["ok"],
            }
            for run in runs
        ],
        "artifacts": artifacts,
    }

    DOCS_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    report_path = DOCS_EVIDENCE_DIR / "toon_wave1_gate_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"report": str(report_path), "repo_map": str(repo_map_path), "runs": report["runs"]}, indent=2))
    print("verify_toon_repo_gate: PASS")


if __name__ == "__main__":
    main()
