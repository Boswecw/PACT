## 30. Dependencies

### Runtime dependencies
PACT uses Python runtime dependencies for schema validation and registry-aware reference handling.

Current known required packages for verification include:
- `jsonschema`
- `referencing`

### Local execution posture
Repo-local virtual environment usage is the preferred execution path for deterministic verification on Ubuntu systems that enforce externally managed system Python environments.

Expected local startup:
```bash
cd ~/Forge/ecosystem/pact
source .venv/bin/activate
```
