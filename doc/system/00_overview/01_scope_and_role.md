## 01. Scope and Role

PACT is a governed internal runtime/service repo within the Forge workspace.

It currently proves and documents these responsibility areas:
- contract validation
- corpus validation
- runtime execution and degradation handling
- replay/live adapter behavior
- telemetry and evidence emission
- export manifests and replay packages
- control-plane catalog, detail, and handoff
- operator API boundary
- deterministic audit transfer bundles
- run-level indexing and audit packaging
- run-level export summary packaging

PACT is not canonical business truth and is not a generic free-running orchestrator. It is a bounded packet/runtime system with explicit audit and operator surfaces.
