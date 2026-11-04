# CVD Boundary 027 — Continuity across Git locations

## Invariant
A GitHub repository rename or transfer is not a new authorship event. A fork is a new repository identity, but it does not erase its source lineage or automatically transfer its source rights.

The numeric GitHub repository ID is the identifier; the mutable `owner/name` path is the locator. Every assertion cites an observed commit SHA. Rename/transfer entries preserve the numeric ID and state their previous name. Fork/derive entries use a new numeric ID and reference a parent repository ID and commit.

Run: `python3 -m unittest -v test_continuity.py`
Validate a JSON file with `{"events":[...]}` using `python3 continuity.py events.json`.

Records are SHA-256 linked claims, not externally certified GitHub observations, legal rights determinations, or proof of first authorship. Commit existence and repository IDs must be checked against GitHub separately. Rewriting all records requires an externally trusted checkpoint to detect. Preserve events append-only; corrections are new records.

FORMIC observes; Jane coordinates derivations; Grandmother preserves lineage. No quorum.
