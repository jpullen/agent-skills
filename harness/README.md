# Test harness

One command tests the graph-prompt kit:

```
pip install -r harness/requirements.txt      # pytest, pyyaml, jsonschema; git 2.31+ must be on PATH
python3 harness/run.py                        # the standard tier
python3 harness/run.py full                   # before a release, or after touching the schema, validate.py or worktrees.py
python3 harness/run.py --list                 # the steps and the exact command behind each
python3 harness/run.py full --only mutation   # one step
```

It exits 0 only when every step passes. `.github/workflows/harness.yml` runs the standard tier on every push and pull request, and the two slow steps of the full tier on pull requests that touch the kit.

## What each tier runs

| Tier | Step | What it shows | Where it lives |
|---|---|---|---|
| fast | consistency | The repository's statements about itself agree: the two schema copies, plugin / prompt / background / changelog versions, the changelog against the background's, the recorded prompt word count, every path and `worktrees.py` command the skills name, every cross-file rule listed, enforced and tested, every `verify` finding and exit code tested, the README's test counts, TEST-MATRIX totals, the worktree example against its generator | `harness/test_consistency.py` |
| fast | record scripts suite | `validate.py` (schema + X01–X37), `coverage.py`, `report.py`, `gen_fixtures.py` | `plugins/graph-prompt/skills/graph-record/scripts/test_*.py` |
| fast | worktrees.py suite | every subcommand, exit code and `verify` finding, against throwaway repositories | `…/graph/scripts/test_worktrees.py` |
| fast | examples | both bundled records validate, cover every rule and report `status: complete` | `…/graph-record/scripts/example*/` |
| fast | codex adapter suite | the Codex adapter's preflight, import and release-layout tests, against this repository's record tools | `compat/codex/tests/` |
| standard | end-to-end scenarios | whole v3.6 runs, driven by a scripted lead with scripted builders: real worktrees, real gates, a real record, both audits, landing and cleanup | `…/graph/scripts/test_e2e_run.py`, `e2e/` |
| full | generated mutants | every schema-derived mutant of both example records is caught or expected to survive: `gaps 0; over-strict 0` | `…/graph-record/scripts/gen_fixtures.py` |
| full | worktrees.py mutation | every single-site mutant of `worktrees.py` is killed by its suite or listed, with a reason, as equivalent | `…/graph/scripts/mutate_worktrees.py`, `equivalent-mutants.json` |

## The end-to-end scenarios

`e2e/lead.py` is a lead with no model in it. It follows the prompt's order — start, baseline (every gate red by assertion against a stub), one branch and one commit per attempt, scope diff and gate, record after every terminal state, integration, both audits, landing, cleanup — calling `worktrees.py` for every git step and writing a record that `validate.py`, `worktrees.py verify`, `coverage.py` and `report.py` then judge. `e2e/builders.py` holds the builders: plain functions that write files. The scripted evidence audit reruns every cited command as written.

| Scenario | From | Asserts |
|---|---|---|
| run 13 replay | run 13 (I03, I12) | a planted out-of-scope write fails the scope diff before any dependent runs; its undo passes from the scope base; a builder stopped after writing is committed and gated; both upstreams reach the join; the planted file never converges; branches outlive worktrees |
| killed before writing | RF-65, G35 | an attempt that changed nothing is a failed row whose commit is its base, and the retry stacks on it |
| upstream reopened | cause (b), RF-67 | the dependent is rebuilt on the re-accepted upstream, its own earlier work stays visible to the scope diff, integration is rebuilt |
| late correction | D23, D69 | a stale integration branch fails `verify` (W05); the next attempt starts from the run base |
| person's branch moved | D70 | delivery is `not_landed`, the person's checkout is untouched, the integration branch is delivered by name |
| conflicting write | D69 | a fan-in over an out-of-scope write conflicts, aborts and leaves a clean tree |
| history gate and squash | run 14 (RF-73), D72 | a file planted by a failed attempt is absent from the integration tree and present in its history; the history gate fails on that commit; the squashed landing publishes one commit without it |
| reset git identity | runs 14 and 15 (RF-74, RF-75), D73 | a changed git identity makes the commit step refuse; the lead restores the given author under a decision and commits again; no commit carries the wrong author |

To add one: write the builders it needs in `e2e/builders.py`, then a test in `test_e2e_run.py` that drives `Lead` and ends with `finish(lead)` or `audits_hold(lead)`.

## What the harness cannot show

It never runs a model. Whether a model follows the prompt as lead, builder or reviewer — a mutant caught, a brief obeyed, a resume planned correctly — is measured by calibration runs, pre-registered and reported in `CALIBRATION-LOG.md`; `TEST-MATRIX.md` lists what those runs have and have not covered. The division of labour: a defect a run finds in the kit becomes a test here (run 13's eight are all in these suites; the ninth, RF-67, was found by the upstream-reopened scenario itself; run 14's history and author findings each have a scenario), and a question about model behaviour becomes a pre-registered test there.

`compat/codex/` works in place against this repository's kit, and its suite runs in the fast tier. `compat/codex/scripts/test_release.py --output DIR` is its own release runner (the record suite, the example and the generated mutants, with a receipt); the harness's full tier covers the same ground.

## When a step fails

- **consistency**: the message names the two places that disagree; change the stale one. A prompt edit needs the changelog's word count; a new test needs the README's count.
- **generated mutants**, a gap: `validate.py` misses something the schema requires. Over-strict: the validator requires a field the schema marks optional; either the schema is wrong or the cross-file rule belongs in `gen_fixtures.CROSSFILE_REQUIRED`.
- **mutation**, an unexpected survivor: write the test that kills it, or, if no test can tell it from the original, add it to `equivalent-mutants.json` with the reason. A stale entry: delete it.
