# CVD 038 — FORMIC Crash Recovery

**Invariant:** `Failure -> Preserve -> Recover -> Continue`, without rewriting an existing witness.

A partial local run can leave observation JSON committed to the working tree while its temporal overlay or causal sidecar is missing. `cvd/recover038.py` reconciles those missing append-only outputs before FORMIC starts another Git scan.

## Recovery preflight

1. Read and verify each of the six witness chains (`ff`, `fr`, `cf`, `cr`, `rf`, `rr`), including SHA256 links and filename identity.
2. Verify each temporal record against its referenced original witness; require a valid append-order chain.
3. Verify existing causal records using `formic036.inspect_existing`; orphan or modified sidecars cause **HOLD**.
4. Optionally compare each witness against a separately retained **trusted** checkpoint, including its count and pinned record SHA.
5. With `--apply`, append missing temporal records and bounded causal evidence through **exclusive, temp-file + hard-link creation**. Existing files are never overwritten.
6. Reinspect all channels after recovery. Report any remaining causal backlog. Unavailable GitHub ancestry is recorded as a causal `HOLD` sidecar.

The default mode is read-only. No new observation is fabricated during recovery; missing evidence is derived solely from already recorded witnesses. The scheduled GitHub Actions workflow runs this step before fresh observations and includes `test_recover038.py`.

### Commands

```bash
cd cvd && python -m unittest -v test_recover038.py
cd ..
python cvd/recover038.py --root .
python cvd/recover038.py --root . --max-closures 12 --apply
python cvd/recover038.py --root . --checkpoint /separately-retained/cvd038-anchor.json --apply
```

### Trusted anchor format (example only)

```json
{"schema":"CVD-RECOVERY-ANCHOR-038-v1","channels":{"ff":{"count":1,"head_record_sha256":"<64-character SHA256>"}}}
```

The anchor must be retained and authenticated **outside the mutable witness repository**. The example is not a valid live checkpoint and the workflow does not automatically possess such an external anchor.

### Limits

This is process-interruption recovery, not a guarantee against storage destruction, malicious full-chain rewrite, or failure between Git local commit and remote push. Git history and an independently administered checkpoint remain necessary. The GitHub workflow has been updated but no successful GitHub Actions execution was confirmed in this chat. The 15 new regression tests were authored; their execution in the committed environment is not yet confirmed. No legal copyright or first-authorship determination is made.
