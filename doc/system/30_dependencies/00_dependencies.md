## 30. Dependencies

### Runtime and verification dependencies
PACT is intentionally lightweight, but verification and schema enforcement do require a small Python dependency set.

Repo-local dependency file:
- `requirements-dev.txt`

Current dependency set:
- `jsonschema`
- `referencing`
- `mypy`

### Local execution posture
Repo-local virtual environment usage is the preferred execution path for deterministic verification on Ubuntu systems that enforce externally managed system Python environments.

Expected local startup:
```bash
cd ~/Forge/ecosystem/pact
source .venv/bin/activate