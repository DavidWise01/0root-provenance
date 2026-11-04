# CVD 030 — Witness divergence without quorum

Constant Velocity Diamond / FORMIC / Jane / Grandmother.

Each witness (ff, fr, cf, cr, rf, rr) retains its own append-only hash chain. Grandmother stores the individual observations. Jane compares the latest records for an event without a vote, quorum, or deletion. Agreement is not proof.

Usage:
```bash
cd cvd
python -m unittest -v test_witness030.py
python witness030.py validate example-ledger.json
python witness030.py compare example-ledger.json CVD-030-DEMO-001
```

Comparison states: CONSISTENT_REPORTS, DIVERGENT_REPORTS, DIFFERENT_TARGETS, NO_OBSERVATIONS, INVALID.

Different commits or repository IDs can mean different observation targets, not misconduct. A reported VERIFIED is still a witness's assertion until externally checked with attest.py / remote_checkpoint.py. The example is SYNTHETIC; it makes no live witness claim.

SHA-256 chaining alone cannot detect a complete replacement with recomputed hashes. Preserve a separately pinned checkpoint. Repository custody does not grant source ownership. Do not overwrite existing attribution or witness records. Each published observation should have a unique immutable Git filename.
