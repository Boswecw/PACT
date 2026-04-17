from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = ROOT / "harness" / "regression" / "context_connectivity_cases.jsonl"
REPORT_FILE = ROOT / "harness" / "regression" / "context_connectivity_verification_report.json"


def fail(msg: str) -> int:
    print(f"VERIFY FAIL: {msg}")
    return 1


def load_cases() -> list[dict]:
    return [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    sys.path.insert(0, str(ROOT))

    from runtime.engine import execute_slice_07  # noqa: WPS433
    from runtime.validation.schema_validator import validate_instance  # noqa: WPS433

    edge_dir = ROOT / "99-contracts" / "fixtures" / "edge"
    edge_checks = [
        (
            json.loads((edge_dir / "packet_base.edge_context_connectivity.json").read_text(encoding="utf-8")),
            "packet_base.schema.json",
        ),
        (
            json.loads((edge_dir / "runtime_receipt.edge_context_connectivity.json").read_text(encoding="utf-8")),
            "runtime_receipt.schema.json",
        ),
        (
            json.loads((edge_dir / "safe_failure_packet.edge_context_connectivity.json").read_text(encoding="utf-8")),
            "safe_failure_packet.schema.json",
        ),
    ]
    for payload, schema_name in edge_checks:
        validate_instance(payload, schema_name)

    cases = load_cases()
    results: list[dict] = []

    for case in cases:
        result = execute_slice_07(case["input"])
        packet = result["packet"]
        receipt = result["receipt"]
        expect = case["expect"]

        kind = "success" if result["ok"] else "safe_failure"
        if kind != expect["kind"]:
            return fail(f"{case['case_id']} kind mismatch")

        if packet.get("task_intent_id") != expect["task_intent_id"]:
            return fail(f"{case['case_id']} packet task_intent_id mismatch")
        if packet.get("context_bundle_id") != expect["context_bundle_id"]:
            return fail(f"{case['case_id']} packet context_bundle_id mismatch")
        if packet.get("context_bundle_hash") != expect["context_bundle_hash"]:
            return fail(f"{case['case_id']} packet context_bundle_hash mismatch")

        if receipt.get("task_intent_id") != expect["task_intent_id"]:
            return fail(f"{case['case_id']} receipt task_intent_id mismatch")
        if receipt.get("context_bundle_id") != expect["context_bundle_id"]:
            return fail(f"{case['case_id']} receipt context_bundle_id mismatch")
        if receipt.get("context_bundle_hash") != expect["context_bundle_hash"]:
            return fail(f"{case['case_id']} receipt context_bundle_hash mismatch")

        if kind == "safe_failure":
            if packet["failure_state"] != expect["failure_state"]:
                return fail(f"{case['case_id']} failure_state mismatch")
            if packet["public_reason_code"] != expect["public_reason_code"]:
                return fail(f"{case['case_id']} public_reason_code mismatch")

        results.append(
            {
                "case_id": case["case_id"],
                "kind": kind,
                "packet_id": packet.get("packet_id") or packet.get("failure_packet_id"),
                "receipt_id": receipt["receipt_id"],
                "task_intent_id": packet.get("task_intent_id"),
                "context_bundle_id": packet.get("context_bundle_id"),
                "context_bundle_hash": packet.get("context_bundle_hash"),
            }
        )

    base_input = {
        "packet_class": "answer_packet",
        "consumer_identity": "authorforge",
        "permission_context": {"tenant": "demo", "scope": "workspace"},
        "serialization_profile": "plain_text_only",
        "now": "2026-04-16T01:03:00Z",
        "task_intent_id": "intent_scene_polish_v1",
        "compile_input": {
            "task_goal": "Answer the user question using grounded support.",
            "instruction_block": "Summarize only the cited material.",
            "support_blocks": ["Source A", "Source B"],
            "grounding_refs": [
                {
                    "grounding_id": "g_001",
                    "source_ref": "doc://alpha",
                    "authority_class": "primary",
                    "excerpt": "Alpha evidence excerpt",
                    "start_offset": 0,
                    "end_offset": 22,
                }
            ],
            "answer_constraints": ["No speculation", "Stay concise"],
        },
    }
    first = execute_slice_07(
        {
            **base_input,
            "context_bundle_id": "ctxb_aaaa1111bbbb2222",
            "context_bundle_hash": "aaaa1111bbbb2222",
        }
    )
    second = execute_slice_07(
        {
            **base_input,
            "context_bundle_id": "ctxb_cccc3333dddd4444",
            "context_bundle_hash": "cccc3333dddd4444",
        }
    )
    if not first["ok"] or not second["ok"]:
        return fail("packet identity proof setup failed")
    if first["packet"]["packet_id"] == second["packet"]["packet_id"]:
        return fail("packet_id did not change when context_bundle_id changed")
    if first["receipt"]["receipt_id"] == second["receipt"]["receipt_id"]:
        return fail("receipt_id did not change when context_bundle_id changed")

    report = {
        "total_cases": len(cases),
        "results": results,
        "packet_identity_change_proved": True,
        "first_packet_id": first["packet"]["packet_id"],
        "second_packet_id": second["packet"]["packet_id"],
        "first_receipt_id": first["receipt"]["receipt_id"],
        "second_receipt_id": second["receipt"]["receipt_id"],
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("CONTEXT CONNECTIVITY OVERLAY VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
