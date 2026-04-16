#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$DOC_DIR/.." && pwd)"
DESIGNATION="PAC"
OUTPUT_PATH="$DOC_DIR/${DESIGNATION}SYSTEM.md"

REQUIRED_DIRS=(
  "$SCRIPT_DIR/00_overview"
  "$SCRIPT_DIR/10_service-contract"
  "$SCRIPT_DIR/20_runtime"
  "$SCRIPT_DIR/30_dependencies"
  "$SCRIPT_DIR/40_governance"
  "$SCRIPT_DIR/50_operations"
  "$SCRIPT_DIR/99_appendices"
)

REQUIRED_FILES=(
  "$SCRIPT_DIR/00_overview/00_repo_identity.md"
  "$SCRIPT_DIR/00_overview/01_scope_and_role.md"
  "$SCRIPT_DIR/10_service-contract/00_service_contract.md"
  "$SCRIPT_DIR/20_runtime/00_runtime_topology.md"
  "$SCRIPT_DIR/30_dependencies/00_dependencies.md"
  "$SCRIPT_DIR/40_governance/00_governance_and_controls.md"
  "$SCRIPT_DIR/50_operations/00_operations_and_verification.md"
  "$SCRIPT_DIR/99_appendices/00_appendix_repo_layout.md"
)

for dir_path in "${REQUIRED_DIRS[@]}"; do
  if [[ ! -d "$dir_path" ]]; then
    echo "BUILD FAIL: missing required directory: $dir_path" >&2
    exit 1
  fi
done

for file_path in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$file_path" ]]; then
    echo "BUILD FAIL: missing required file: $file_path" >&2
    exit 1
  fi
done

{
  echo "# PACSYSTEM"
  echo
  echo "- Repository: PACT"
  echo "- Designation: PAC"
  echo "- Repo class: service / internal runtime"
  echo "- Canonical artifact path: doc/PACSYSTEM.md"
  echo "- Build entry: doc/system/BUILD.sh"
  echo "- Date: 2026-04-15"
  echo "- Time: 07:58:08 PM America/New_York"
  echo
  for file_path in "${REQUIRED_FILES[@]}"; do
    echo "---"
    echo
    cat "$file_path"
    echo
  done
} > "$OUTPUT_PATH"

echo "BUILD OK: wrote $OUTPUT_PATH"
