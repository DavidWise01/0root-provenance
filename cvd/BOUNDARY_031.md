# CVD 031 — Natural Invariant: Continuous Git Witness

`Observe → Verify → Append only if changed`

FORMIC reads public GitHub repositories and their current default-branch commit SHA. The collector uses the configured witness channel (ff, fr, cf, cr, rf, or rr), checks its local history, and creates one immutable JSON observation per changed source state. No votes. No quorum. One process does not pretend to be three independent witnesses.

- Collector: [collect031.py](collect031.py)
- Regression suite: [test_collect031.py](test_collect031.py)
- Scheduled GitHub Action: [cvd-formic-031.yml](../.github/workflows/cvd-formic-031.yml)
- Observations: `cvd/observations/<witness>/<sequence>-<hash>.json`

The GitHub Action is scheduled every six hours and can be invoked manually. It commits at most 250 newly observed records per run. This schedule is a committed configuration, not proof that a run has executed or succeeded. A GitHub Actions token must be permitted to push commits for automated publication. GitHub may defer scheduled jobs.

The collector records observations for public repositories only and never overwrites an existing observation file. It does not claim legal title, creator identity, or first publication. A GitHub-observed commit means only that the stated commit existed in the queried repository when observed. The collector emits HOLD for unavailable evidence rather than treating unavailable observations as verified. A prior externally held checkpoint is still required to detect a wholesale rewritten history.

### Baseline local tests (separate local prototype)

12/12 regression tests passed. A synthetic 2,132-repository dry run yielded 2,132 new observations on its first pass and zero on an unchanged second pass. Local timing is not GitHub API throughput. The committed variant requires its own CI run to confirm remote execution.
