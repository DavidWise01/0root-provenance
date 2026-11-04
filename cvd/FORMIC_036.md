# FORMIC 036 — Integrated Six-Channel Git Perimeter

**Invariant:** Observe public Git → preserve one actual witness → reconcile event/append clocks → fetch bounded Git ancestry → append causal evidence → compare all six channels without quorum → publish append-only Git records.

The workflow `.github/workflows/cvd-formic-031.yml` now has six UTC schedule slots, one real execution per witness channel:

| UTC schedule | Channel |
|---|---|
| 00:17 | ff |
| 04:17 | fr |
| 08:17 | cf |
| 12:17 | cr |
| 16:17 | rf |
| 20:17 | rr |

Manual workflow_dispatch selects one channel explicitly. GitHub Actions is a scheduler and automation service; these are six separate *runs*, not independently administered third-party witnesses. A channel can be empty until its scheduled job successfully runs. The existing public-only collector never lists private repositories in the published report.

The unified executable is `cvd/formic036.py` (dry run by default). `--apply` appends observations, temporal overlays, and bounded causal sidecars. Existing observations are not overwritten. `cvd/formic_compare036.py --apply` creates a content-addressed comparison report, with no consensus or majority semantics. These reports are readable through `cvd/formic.html` and linked from `cvd/index.html`.

Default causal budgets: 12 root-head records per run, 12 Git commit objects per closure, max depth 5. A limit or GitHub unavailability yields **HOLD** for ancestry rather than full verification; backlog is reported for later runs. All six channels' complete historical coverage is *not yet verified*.

Run locally from repository root:

```bash
cd cvd && python -m unittest -v test_collect031.py test_reconcile033.py test_closure035.py test_formic036.py test_formic_compare036.py
cd ..
python cvd/formic036.py --observer ff
python cvd/formic036.py --observer ff --apply
python cvd/formic_compare036.py --apply
```

Applying requires appropriate GitHub API access. The scheduled GitHub Action requires repository permissions permitting `GITHUB_TOKEN` to push to the default branch. Configuring a schedule does **not** prove it has run, succeeded, or deployed GitHub Pages.

**Evidence limitations:** SHA256 chains do not stop coordinated wholesale rewrites absent independently held checkpoints. GitHub's Git Commit API is not an independent cryptographic proof of original authorship, rights, priority or legal ownership. No quorum; original claims and contradictory observations are preserved.
