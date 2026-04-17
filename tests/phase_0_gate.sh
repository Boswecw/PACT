#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "PHASE_0_GATE_FAIL: $1" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing file: $path"
}

require_line() {
  local needle="$1"
  local path="$2"
  grep -Fq "$needle" "$path" || fail "missing marker in $path :: $needle"
}

ACCEPTANCE_FILE="docs/implementation/hermes_openclaw/phase_0_acceptance.md"

require_file "spec.md"
require_file "todo.md"
require_file "$ACCEPTANCE_FILE"
require_file "tests/phase_0_gate.sh"

require_line "decision_lock_status: accepted" "$ACCEPTANCE_FILE"
require_line "proving_slice_status: accepted" "$ACCEPTANCE_FILE"
require_line "repo_split_status: accepted" "$ACCEPTANCE_FILE"
require_line "proving_slice: documentation-drift-digest" "$ACCEPTANCE_FILE"

require_line "no_master_orchestrator_above_yellowjacket: true" "$ACCEPTANCE_FILE"
require_line "yellowjacket_sole_runtime_admission_point: true" "$ACCEPTANCE_FILE"
require_line "openclaw_requests_are_intents_only: true" "$ACCEPTANCE_FILE"
require_line "openclaw_direct_to_hermes_bypass_forbidden: true" "$ACCEPTANCE_FILE"
require_line "hermes_executes_yellowjacket_issued_packets_only: true" "$ACCEPTANCE_FILE"
require_line "memory_v1_disabled: true" "$ACCEPTANCE_FILE"
require_line "subagents_v1_forbidden: true" "$ACCEPTANCE_FILE"

echo "PHASE_0_GATE_PASS"
