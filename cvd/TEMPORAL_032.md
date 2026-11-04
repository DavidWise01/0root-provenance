# CVD 032 — Temporal Witness Continuity

The new invariant distinguishes three times: reported event time (optional), observation time, and the time an observation was appended. It is an append-only overlay referencing legacy FORMIC records by SHA-256. No old record is overwritten.

A delayed record may have an earlier observation timestamp than another record in the same witness chain. Appended timestamps, however, must remain nondecreasing within a witness's chain. Disagreement at a shared timestamp is recorded as SAME_TIME_DIVERGENCE; differing commits observed at different times are TEMPORAL_VARIATION. Neither is proof of misconduct.

Usage: `cd cvd && python -m unittest -v test_temporal032.py`. The standalone comparator accepts `python temporal032.py ledger.json 123`, where 123 is a numeric GitHub repository ID and ledger.json contains `{"records":[...]}`.

Witness timestamps are assertions, not trusted time-server attestations. The original Git SHA and witness record SHA must be independently checked; this module performs local validation only. A separately retained checkpoint remains necessary to detect wholesale history rewriting. This is not proof of legal authorship or title.

FORMIC witnesses observe independently, Jane analyzes deltas, and Grandmother preserves all records. No quorum.
