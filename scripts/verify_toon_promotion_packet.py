from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"

REQUIRED_ARTIFACTS = [
    "docs/evidence/toon_wave1_operator_examples.md",
    "docs/evidence/toon_observability_report.json",
    "docs/evidence/toon_wave1_gate_report.json",
    "docs/evidence/toon_wave1_repo_map.md",
    "docs/evidence/toon_extension_governance_report.json",
    "doc/system/10_service-contract/01_receipt_serialization_evidence_strategy.md",
    "doc/system/20_runtime/01_runtime_serialization_boundary.md",
    "doc/system/40_governance/01_toon_wave1_rollout_and_feature_flag.md",
    "doc/system/40_governance/02_toon_extension_admission_policy.md",
    "doc/system/50_operations/01_toon_wave1_proof_gate.md",
    "doc/system/50_operations/03_toon_wave1_promotion_packet.md",
    "runtime/rendering/toon_registry.json",
    "99-contracts/schemas/toon_registry_wave1.schema.json",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_upstream_artifacts() -> None:
    env = os.environ.copy()
    env["PACT_ENABLE_TOON_WAVE1"] = "true"

    for rel_path in [
        "scripts/verify_toon_wave1.py",
        "scripts/verify_toon_observability.py",
        "scripts/verify_toon_extension_governance.py",
    ]:
        proc = subprocess.run(
            [sys.executable, rel_path],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
        )
        _assert(
            proc.returncode == 0,
            f"upstream verifier failed: {rel_path}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )


def main() -> None:
    _ensure_upstream_artifacts()

    packet_entries = []
    for rel in REQUIRED_ARTIFACTS:
        path = REPO_ROOT / rel
        _assert(path.exists(), f"required artifact missing: {rel}")
        packet_entries.append(
            {
                "path": rel,
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
        )

    packet = {
        "promotion_packet": "toon_wave1",
        "packet_version": "1.0.0",
        "all_green": True,
        "entries": packet_entries,
    }

    DOCS_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_EVIDENCE_DIR / "toon_wave1_promotion_packet.json"
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    _assert(loaded["promotion_packet"] == "toon_wave1", "promotion packet id mismatch")
    _assert(len(loaded["entries"]) == len(REQUIRED_ARTIFACTS), "promotion packet entry count mismatch")

    print(json.dumps({"promotion_packet": str(out_path), "entries": len(loaded["entries"])}, indent=2))
    print("verify_toon_promotion_packet: PASS")


if __name__ == "__main__":
    main()
