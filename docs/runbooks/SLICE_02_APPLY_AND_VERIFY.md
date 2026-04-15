# Slice 02 Apply and Verify

Run from the PACT repo root after Slice 01 is already present:

```bash
unzip -o slice_02_pact_contract_validation_and_corpus_runner.zip
python3 scripts/verify_slice_02.py
```

Manual commands:

```bash
python3 scripts/validate_contract_fixtures.py
python3 scripts/lint_corpus.py
cat 99-contracts/schema_validation_report.json
cat corpus/corpus_lint_report.json
```
