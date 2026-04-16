## 20. Runtime Topology

### Runtime lanes
Primary runtime ownership is expressed across these repo surfaces:
- `runtime/`
- `control-plane/`
- `adapters/`
- `telemetry/`
- `harness/`
- `scripts/`

### Behavioral posture
PACT executes with fail-closed validation, explicit degradation states, replay/live separation, deterministic artifact writing, and operator-readable evidence.

### Current verified runtime scope
The verified runtime path now includes:
- compile and validation flow
- retrieval and budget handling
- replay/live provider resolution
- telemetry and evidence bundles
- run indexing
- audit transfer packaging
- run export summary packaging
