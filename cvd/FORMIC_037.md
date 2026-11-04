# CVD 037 — Operational Attestation

**Invariant:** A configured or started FORMIC GitHub Action is not evidence of a completed successful observation.

A retrospective receipt is created only from GitHub Actions REST metadata for a **previously completed** execution. The running job explicitly excludes its own `github.run_id` and does not claim that its current Git push succeeded. Each attempt is recorded separately at `cvd/operations/github-actions/<run-id>-<attempt>.json`, and existing receipt files are checked rather than overwritten.

The receipt records run identity, attempt, triggering event, head commit SHA, GitHub-reported conclusion, timestamps, and the official run URL. Success is labeled `REPORTED_SUCCESS` because it is GitHub's report, not an independent attestation. Failures, cancellations, and timed-out runs remain evidence as `REPORTED_NON_SUCCESS`. Pending runs are omitted, not counted as success. Unknown or malformed completed metadata stops the attestation step with HOLD.

## Workflow

`.github/workflows/cvd-formic-031.yml` invokes `cvd/operations037.py --apply --current-run-id "$RUN_ID"` after FORMIC observation and comparison, but before the Git append. If GitHub's Actions API cannot provide valid data, the evidence step logs HOLD and allows existing witness records to be committed. Thus operational receipts are best effort, not a precondition of preserving witness observations.

The job's prior metadata receipts do not prove that individual repository observations are complete, that GitHub Pages deployed, or that legal ownership belongs to a claimant. GitHub Action tokens must have permission to read Actions metadata and push to the repository. The current chat has no verified live Actions run history.

## Local use

```bash
cd cvd
python -m unittest -v test_operations037.py
cd ..
python cvd/operations037.py --root .
python cvd/operations037.py --root . --apply
```

Use `GITHUB_TOKEN` or `GH_TOKEN` for authenticated API access. The script retrieves the most recent 100 workflow runs, so it is **not** an exhaustive historic audit. Existing stored receipts are revalidated, and a missed run can only be recovered while it remains discoverable in that bounded API window.

No witness votes. Each factual observation and reported workflow outcome is preserved individually. A SHA256 record alone is not a signed trusted time or legal title certificate.
