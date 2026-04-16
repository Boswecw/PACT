## 50. Operations and Verification

### Standard operator workflow
1. enter repo root
2. activate `.venv`
3. run slice verification
4. run mypy
5. rebuild `doc/PACSYSTEM.md` after documentation edits

### Standard verification commands
```bash
python3 scripts/verify_slice_12.py
python3 -m mypy runtime scripts
bash doc/system/BUILD.sh
```

### Expected success state
A healthy repo state for the current slice proves:
- Slice 12 verification passes
- mypy passes
- canonical documentation build succeeds
