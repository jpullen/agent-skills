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
| standard | synthetic suite tests | the scenario suite's own tests: the catalog is deterministic and covers every factor pair, a scenario reproduces to the commit, the oracle fails a planted wrong behaviour, `compare` reports a changed field | `…/graph/scripts/test_synth.py` |
| standard | synthetic scenarios (sample) | 12 of the 67 synthetic scenarios, each checked against its oracle and compared with the committed baseline | `harness/scenarios.py`, `…/graph/scripts/synth/` |
| full | synthetic scenarios (all) | all 67, against the oracle and the baseline; the results file is kept as a CI artifact | as above, `harness/scenarios-baseline.json` |
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

## The synthetic scenario suite

`harness/scenarios.py` generates and runs a suite of whole v3.6 runs that is the same on every machine, so two runs can be compared field by field.

```
python3 harness/scenarios.py list                                  # the 67 scenarios, their faults and corruptions
python3 harness/scenarios.py run --out new.json                    # run all, check each against its oracle
python3 harness/scenarios.py run --compare harness/scenarios-baseline.json   # and compare with the baseline
python3 harness/scenarios.py run --only diamond named- --jobs 4    # a subset
python3 harness/scenarios.py compare old.json new.json             # two result files, scenario by scenario
python3 harness/scenarios.py coverage new.json                     # what the suite exercised
```

**What a scenario is.** A graph shape, faults placed on its nodes, a delivery mode, and a list of record corruptions. `synth/engine.py` builds a throwaway repository and runs it through the real kit with a scripted lead: start, baseline, one branch and one commit per attempt, the scope diff and the gate, the record after every state change, integration, both audits, the history gate, landing and cleanup. It then applies each corruption to a copy of the finished record and runs `validate.py` and `worktrees.py verify` on the copy. Every node writes `out/<node>.txt`, holding a value derived from its upstreams' values, so any shape works without code written for it.

**How the suite is generated** (`synth/catalog.py`). The levels are:

| Factor | Levels |
|---|---|
| shape | single, chain, join, diamond, fan3, deep, wide |
| fault | none, wrong value, out-of-scope write, builder stopped before writing, builder stopped after writing, leaked secret, wrong upstream value (cause b), conflicting write, correction after integration |
| position | root, middle, sink |
| extra | none, reset git identity |
| delivery | fast-forward, squash, person's branch moved |

A greedy all-pairs cover picks 60 combinations that exercise every valid pair of levels: 201 pairs. Seven named scenarios add compound faults, a refused start, a dirty cleanup and a gate that leaves byproducts. Fourteen record corruptions are spread over the scenarios they apply to, up to three each.

**What counts as passing.**
- **Oracle check.** `catalog.expected()` derives, from the scenario alone and from the prompt's rules, what must happen. That covers each node's attempts and their verdicts, the number of integrations, whether the history gate fails, how delivery lands, which `worktrees.py` exit codes occur, conflict and stale-integration probes, clean audits, and the findings each corruption must produce. A mismatch is a defect in the kit, the engine or the oracle; they were written separately so that they can disagree.
- **Baseline comparison.** The fingerprint holds every attempt's commit id, the order of every `worktrees.py` call and its exit code, the integration order, the landed commit, the final branches, and the audit and corruption findings. It holds no path, time or random value. Git runs with fixed dates and no user or system config, so commit ids are reproducible. Two runs of an unchanged kit produce identical files: checked with 4 and with 3 workers.

**Coverage reported at the end of every run.** These figures are against what exists, not against a list chosen to look good:
- `worktrees.py` exit codes: 20 of 20.
- `verify` findings W01–W10: 9 of 9 that the source emits.
- Worktree validator rules X34–X37: 4 of 4.
- 18 named transitions of the run's state machine: 18 of 18.
- Factor pairs: 201 of 201.

**Changing the baseline.** A difference from `harness/scenarios-baseline.json` is either a regression or an intended change. When it is intended, the procedure is:
1. Read the `compare` output.
2. Run `python3 harness/scenarios.py run --out harness/scenarios-baseline.json`.
3. Commit the baseline with the kit change, naming the scenarios that changed and why.

Editing `catalog.py` changes the suite digest, and `compare` then says so before listing scenarios added and removed. To compare two CI runs, download each run's `harness-full` artifact and run `compare` on the two `scenarios.json` files.

## What the harness cannot show

It never runs a model. Whether a model follows the prompt as lead, builder or reviewer — a mutant caught, a brief obeyed, a resume planned correctly — is measured by calibration runs, pre-registered and reported in `CALIBRATION-LOG.md`; `TEST-MATRIX.md` lists what those runs have and have not covered. The division of labour: a defect a run finds in the kit becomes a test here (run 13's eight are all in these suites; the ninth, RF-67, was found by the upstream-reopened scenario itself; run 14's history and author findings each have a scenario), and a question about model behaviour becomes a pre-registered test there.

`compat/codex/` works in place against this repository's kit, and its suite runs in the fast tier. `compat/codex/scripts/test_release.py --output DIR` is its own release runner (the record suite, the example and the generated mutants, with a receipt); the harness's full tier covers the same ground.

## When a step fails

- **consistency**: the message names the two places that disagree; change the stale one. A prompt edit needs the changelog's word count; a new test needs the README's count.
- **generated mutants**, a gap: `validate.py` misses something the schema requires. Over-strict: the validator requires a field the schema marks optional; either the schema is wrong or the cross-file rule belongs in `gen_fixtures.CROSSFILE_REQUIRED`.
- **mutation**, an unexpected survivor: write the test that kills it, or, if no test can tell it from the original, add it to `equivalent-mutants.json` with the reason. A stale entry: delete it.
