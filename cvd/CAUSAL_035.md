# CVD 035 — Git Causal Closure

**Invariant:** A claimed parent edge is not proven until a GitHub commit object is read and its parent SHA is verified. The verifier follows the *GitHub REST Git Commit API* for each parent link, including merges. The query is bounded by maximum nodes and maximum depth.

- VERIFIED: all reachable parents within scope were read and the graph reached roots without errors.
- HOLD: a parent was unavailable, malformed, mismatched, or blocked by the traversal bounds.
- REJECT: a cycle was detected in the supplied GitHub responses.

No witnesses vote. Each outcome is evidence of one observation, not copyright ownership, creation priority, or an independently signed attestation. The result contains a SHA256 digest but is not tamper-proof without an externally retained trusted checkpoint. A `VERIFIED` result is a bounded GitHub API observation; the verifier does not check Git cryptographic object serialization locally.

Usage with GitHub network access and optional GITHUB_TOKEN:
```bash
python cvd/closure035.py DavidWise01/0root-provenance <40-character-commit> --max-nodes 200 --max-depth 20 --output cvd-closure.json
cd cvd && python -m unittest -v test_closure035.py
```
The output filename is created exclusively and cannot overwrite an existing observation. The GitHub-scheduled FORMIC collector has **not** been modified to call this tool automatically.

FORMIC independently observes, Jane analyzes, Grandmother preserves the individual record. No quorum.
