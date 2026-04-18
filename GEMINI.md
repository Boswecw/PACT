# GEMINI.md
Date: 2026-04-17
Time: 03:14 AM America/New_York

## Repo Identity
PACT is part of the BDS / Forge ecosystem.
Treat it as a governed packet / context-carriage / efficiency-sensitive system component.
Do not frame this repo as an MVP or as a generic helper library.

## Primary Working Rules
- Prefer bounded, explicit changes.
- Prefer minimal edits over broad refactors.
- Do not invent packet fields, receipt fields, IDs, hashes, transport assumptions, or cloud/local semantics.
- Preserve packet identity, lineage, and carriage integrity.
- Keep responses copy/paste friendly.
- If a contract detail is uncertain, inspect the repo first.

## Output Contract
- Show the exact file path first when changing files.
- Prefer full-file replacement output when practical.
- Provide exact commands only.
- Do not provide pseudo-commands.
- State root cause before or with the fix when debugging.
- If verification was not run, say so explicitly.

## Repo Purpose
PACT exists to support efficient, disciplined packetized context carriage and related identity/control behavior across local and cloud-connected flows.
Treat it as a contract-sensitive subsystem, not as a loose convenience layer.

## Core Preservation Rules
- Preserve packet identity semantics.
- Preserve bundle/receipt relationships.
- Preserve hash and change-detection meaning.
- Preserve local/cloud handoff discipline.
- Preserve lineage fields and carriage invariants.
- Do not casually merge transport logic, assembly logic, and policy logic.

## Architecture Boundaries
Preserve boundaries between:
- packet construction
- packet identity / hashing
- context carriage
- transport or delivery concerns
- receipt / evidence concerns
- app-specific orchestration concerns

PACT should not absorb unrelated application logic.

## Contract Rules
When changing packet or carriage behavior:
- identify the current contract first
- identify all affected fields explicitly
- preserve backward expectations unless the task explicitly changes the contract
- call out breaking changes clearly
- verify identity and hash behavior explicitly when relevant

Do not casually rename, remove, or repurpose fields.

## Local / Cloud Rules
PACT may participate in both local and cloud-connected flows.
When reasoning about changes:
- separate local-only behavior from cloud-bound behavior
- do not blur the handoff point
- do not assume cloud transport rules should shape local packet identity
- do not assume local optimization should weaken downstream contract clarity

## Efficiency Rules
PACT is efficiency-sensitive.
When making changes:
- preserve the intended token-efficiency and bounded-context posture
- avoid changes that expand packet payloads without a stated reason
- avoid “include everything” solutions
- prefer disciplined, deterministic context shaping

## Provenance and Identity Rules
When identity or lineage fields are involved:
- preserve field stability
- preserve deterministic behavior
- preserve relationship between source bundle, packet, and downstream receipt when that relationship exists
- do not treat provenance as optional metadata

If a field participates in equality, identity, hashing, or routing behavior, treat it as high risk.

## Testing and Verification Rules
Before calling a task done:
1. identify whether the change affects identity, hashing, carriage, or downstream compatibility
2. run the narrowest relevant tests first
3. if a hash or packet identity rule changed, verify before/after behavior explicitly
4. if a connectivity overlay is involved, verify the lineage fields are preserved
5. report exactly what passed or failed

## Cross-Repo Rules
PACT will often sit between systems.
When working cross-repo:
- do not assume both sides interpret the packet identically
- verify field names, field meaning, and lifecycle explicitly
- separate contract mismatch from runtime failure
- separate payload-shape issues from orchestration issues

## Documentation Rules
When creating or updating docs in this repo:
- keep docs aligned to implementation
- do not write aspirational claims
- include date and time
- use direct, operational language

## Context Priorities
When reasoning about PACT, inspect in this order when relevant:
1. target file(s)
2. packet schema / models / contracts
3. identity or hash logic
4. tests covering carriage, identity, or connectivity
5. docs describing packet behavior
6. adjacent integration points

## Do Not
- do not invent packet fields
- do not weaken identity semantics
- do not broaden packet payloads casually
- do not collapse local and cloud concerns into one vague flow
- do not claim compatibility without verification

## Preferred Default Work Pattern
1. Identify whether the task is schema, identity, carriage, receipt, or integration related.
2. Identify the exact files.
3. State the narrow verification target.
4. Make the bounded change.
5. Run or recommend the narrow verification.
6. Report exact results and next step.