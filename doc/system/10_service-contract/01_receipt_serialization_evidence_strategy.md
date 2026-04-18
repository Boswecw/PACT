# Receipt Serialization Evidence Strategy ADR
**Date:** 2026-04-17
**Time:** 20:30 UTC

## Decision
Serialization evidence is carried as a governed nested object inside the runtime receipt.

## Why
Loose top-level fields create drift and weaken compatibility posture.
The nested object preserves requested profile, used profile, render attempt status, fallback status, artifact kind, segment metadata, and token estimates in one controlled contract.

## Consequences
- receipt evolution stays additive and understandable
- operators can inspect rendering behavior without reconstructing it from logs
- future wave extensions must preserve receipt simplicity
