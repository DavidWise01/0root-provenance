# CVD 039 — External Recovery Anchor

**Invariant:** Internal hash-chain integrity is insufficient to detect an attacker who replaces every record and recomputes hashes. A previously retained checkpoint must be held outside the mutable source ledger and verified against an independently supplied digest before accepting recovery.

## Two inputs, not one

1. A canonical immutable checkpoint JSON file in a *different Git repository*, currently supported at `DavidWise01/attribution-standard`, path `cvd/anchors/<name>.json`. Use a **40-character commit SHA** in its raw.githubusercontent.com URL, never `main` or a movable tag.
2. The expected SHA-256 digest of the exact canonical file bytes, retained *out of band*. The script obtains this through `--expected-sha256` or `CVD_EXTERNAL_ANCHOR_SHA256`.

`cvd/external_anchor039.py` checks the remote-byte digest, canonical JSON, complete six-channel set, and that each pinned chain prefix matches the current local history. It does not assume every later witness record has been externally anchored. No quorum.

### Create a genuine checkpoint from a checked-out source ledger

```bash
python cvd/external_anchor039.py --root . --emit /tmp/cvd-formic-anchor.json
```

This creates the file *exclusively*, prints its digest, and labels it `GENERATED_UNTRUSTED` until it is actually retained elsewhere. Publish this file by an authorized operation into the separate repository, retain its SHA-256 digest outside the mutable source repository, and note the publication commit SHA.

A pinned read URL must look like:
```text
https://raw.githubusercontent.com/DavidWise01/attribution-standard/<40-character-commit>/cvd/anchors/<checkpoint-name>.json
```

Then configure these GitHub Actions inputs:
- Repository variable `CVD_EXTERNAL_ANCHOR_URL` = immutable raw Git URL from the published copy.
- Repository secret `CVD_EXTERNAL_ANCHOR_SHA256` = independently retained expected digest.

The scheduled FORMIC workflow verifies the anchor **before** `recover038.py`. If one setting exists without the other, or verification returns HOLD, the job halts before recovery. If neither is set, the workflow is explicitly `UNANCHORED` and continues; it does not represent this as external attestation.

### Limits

The checkpoint currently lives in another GitHub repository under the same account, and the SHA-256 can be stored as a GitHub secret under the same administrative control. That is **cross-repository anchoring**, not independence from a compromised GitHub account. For stronger trust, keep the digest or signed checkpoint in independently administered archival storage. A hash is not a signature, does not prove when the record was created, and does not determine legal copyright ownership.

An anchor represents a **prefix** of each witness history: new appended observations need periodic new independent checkpoints. Existing provenance records are not overwritten. This release adds the verifier and workflow gate; it does *not* claim that a live checkpoint has been installed or that GitHub Actions has succeeded.

### Tests

```bash
cd cvd && python -m unittest -v test_external_anchor039.py
```

The local regression suite includes digest mismatch, broken chains, malformed URLs, schema and channel mismatches, canonical encoding, and append-after-anchor compatibility.
