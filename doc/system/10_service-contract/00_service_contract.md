## 10. Service Contract Surface

### External contract families
PACT owns and enforces machine-readable contract surfaces under `99-contracts/`, including schema validation fixtures and operator-facing request/response shapes.

### Contract responsibilities
- packet schemas and packet-base rules
- runtime receipts
- degradation-state and serialization rules
- grounding and lineage artifacts
- operator API request/response contracts
- export/audit package manifest contracts

### Current proving posture
PACT is green through Slice 12 and has a verification chain that proves compatibility through layered slice verification scripts.
