# TOON Wave 1 Operator Evidence

## Example 1 — TOON success
- requested profile: plain_text_with_toon_segment
- used profile: plain_text_with_toon_segment
- artifact kind: toon_segment
- segment meta: {
  "segment_id": "toonseg_c06e4a63543fa74f",
  "segment_version": "1.0.0",
  "row_definition_id": "ranked_result_row_v1",
  "row_count": 2,
  "source_lineage_digest": "sha256:9045c5175ae1ed3cb197ccf98fd71a38136ebba2d59589d1d6ce94d284cae901",
  "segment_hash": "sha256:0644898231b9c63c5efcf3cb1478e17b29e0aed98c5436bc3e7ca1b152e237eb"
}
- token estimates: {
  "before_tokens": 156,
  "after_tokens": 82,
  "delta_tokens": 74,
  "reduction_percentage": 47.44,
  "estimator_family": "pact_estimate_token_count_v1"
}

## Example 2 — Plain-text fallback
- requested profile: plain_text_with_toon_segment
- used profile: plain_text_only
- fallback reason: toon_disabled
- segment meta: None

## Example 3 — Fail-closed
- requested profile: plain_text_with_toon_segment
- render attempted: True
- artifact emitted: False
- fail-closed reason: serialization_failed
