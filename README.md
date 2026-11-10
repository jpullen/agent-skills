# agent-skills

A Claude Code plugin marketplace with two plugins. `graph-prompt` holds a prompt that runs a multi-step task as a graph of bounded nodes with gated reviews and a YAML run record, plus the scripts that validate that record. `prompt-authoring` holds a rule set for writing durable AI instructions (CLAUDE.md, SKILL.md, prompt files) and a staged analysis pipeline, PIPELINE-001. It is for people who use Claude Code for work whose outputs depend on one another, and for people who write instructions that a model has to keep following. The skills are `SKILL.md` folders in the Agent Skills format, which other agent tools also read; the plugin packaging, the `${CLAUDE_SKILL_DIR}` script paths and some frontmatter keys (`disable-model-invocation`, `allowed-tools`) are Claude Code's, and `compat/codex/` adapts the graph prompt for Codex.

## Install

```
/plugin marketplace add jpullen/agent-skills
/plugin install graph-prompt@jpullen
/plugin install prompt-authoring@jpullen
```

To pick up a newer release, run `/plugin marketplace update jpullen`; Claude Code fetches a new copy of a plugin only when its version changes.

## The four skills

| Skill | Plugin | How it is invoked | Purpose |
|---|---|---|---|
| `graph` | `graph-prompt` | You type `/graph-prompt:graph <task>`. It has `disable-model-invocation: true`, so Claude does not start it on its own. | Run a multi-step deliverable as a bounded-node graph with gated reviews and a validated run record that another session can resume. |
| `graph-record` | `graph-prompt` | Claude loads it when you ask to validate a run record, check whether it is complete, check rule coverage, or produce the delivery report, or when you point at a run directory holding `graph.yaml`, `checks.yaml` and `progress.yaml`. | Validate, report on, and check rule coverage of a graph-prompt run record, using `validate.py`, `coverage.py` and `report.py`. |
| `prompt-authoring` | `prompt-authoring` | Claude loads it when you ask to write, edit, review or audit a CLAUDE.md, SKILL.md, system prompt, rule set, plan template or experiment contract. | Author or revise durable AI instructions to the Prompt Authoring Guide's format rules, or audit existing instructions against them. |
| `pipeline-001` | `prompt-authoring` | You type `/prompt-authoring:pipeline-001`. It has `disable-model-invocation: true`. | Run a staged structured analysis (frame, route expertise, check prior art, analyze, synthesize, adversarial critique, refine, coherence review) on a substantive analytical or design problem. |

## What makes these skills unique

**Reviews are tested before they are trusted.** Each review gate gets two unlabeled variants in random order: the real artifact and a copy with one planted defect. The review counts only if it fails the planted copy and passes the real one; a surviving defect voids it ([`graph` SKILL.md](plugins/graph-prompt/skills/graph/SKILL.md)).

**The run record is checked by code, not by reading.** A [JSON schema](plugins/graph-prompt/skills/graph/references/graph-record.schema.json), the cross-file rules in `validate.py`, `coverage.py` and `report.py` read the record. `gen_fixtures.py` generates mutated records to test the validator: on the bundled example it made 596, of which 591 were expected to be caught and all 591 were, with no gaps. The scripts' 370 tests pass ([scripts](plugins/graph-prompt/skills/graph-record/scripts/)).

**Failures have named causes and a budget.** A retry records one of four causes (builder error, upstream field wrong, check wrong, source defect); a node fails on its third failed attempt; the last tenth of the run limit is reserved; a fresh-context evidence audit re-checks cited commands ([`graph` SKILL.md](plugins/graph-prompt/skills/graph/SKILL.md)).

**Calibrated in the open.** [CALIBRATION-LOG.md](CALIBRATION-LOG.md) records 12 numbered runs with results, failures and costs.

**The authoring guide has history.** The [rule-design standards](plugins/prompt-authoring/skills/prompt-authoring/references/rule-design-standards.md) are at v2.9.0, with a changelog back to v1.0.0, and [PIPELINE-001](plugins/prompt-authoring/skills/pipeline-001/SKILL.md) is a staged analysis that includes prior-art, adversarial-critique and coherence-review stages.

**Related work** (the author's search, November 2026). obra/superpowers' [subagent-driven-development](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) skill also runs a fresh subagent per task with a separate reviewer and a cap on fix rounds; it does not test the reviewer with a planted defect. [Mutation testing of LLM judges](https://agentpatterns.ai/verification/mutation-testing-llm-judges/) uses injected defects as offline calibration of judge setups, not as a gate on each review.

## What a run record is

A graph run writes its state to a directory of YAML files, by default `.graph/<date>-<task-slug>/`: `graph.yaml` (the nodes), `checks.yaml` (the checks and their verdicts), `progress.yaml`, `framing.yaml`, `rules.yaml` and `lessons.yaml`. The files follow a JSON schema that ships with the plugin, and `validate.py` checks them against it and against cross-file rules; a run counts as complete only when `validate.py` exits 0 on its record (plus the other conditions the graph prompt lists). The record, not the session, is the state: a later session resumes, reruns or extends the run by reading it. `coverage.py` lists which rules drawn from the task's sources no check exercises, and `report.py` produces the delivery report from the record. None of the three scripts writes into the run directory.

## Requirements

`python3` and `pyyaml` for the three record scripts; `jsonschema` as well for `validate.py` (see [the graph-record skill](plugins/graph-prompt/skills/graph-record/SKILL.md)). For example: `pip install pyyaml jsonschema`.

## Repository layout

```
.claude-plugin/        marketplace.json
plugins/
  graph-prompt/        plugin: skills graph and graph-record, CHANGELOG.md
  prompt-authoring/    plugin: skills prompt-authoring and pipeline-001, CHANGELOG.md
compat/
  codex/               adapter for running the graph prompt under Codex
CALIBRATION-LOG.md     the author's calibration runs and decisions
TEST-MATRIX.md         what the calibration runs have and have not exercised
ATTRIBUTION.md       lineage and prior art
LICENSE                MIT
PUBLISH.md             commands to publish the repository
```

## When to use the graph

Open a run record when the work has outputs that must be accepted before other outputs build on them, when several sources must be reconciled under separate content and integration checks, or when the work crosses a handoff where someone else will resume from the record. Do not open one for a lookup, a status check, an isolated edit with a known test, or a deterministic batch with one acceptance outcome — size is not the threshold; dependency and acceptance structure are. When a required capability is missing (a fresh reviewer, a source, capacity for the audits), do the independent preparation, record the unavailable gate, and do not call a direct result a graph completion. A person's choice of method controls. The prompt's "one node is a valid graph" is for the case where the record itself is wanted; it is not a floor.

**Measured once (run 12, pre-registered, one pair).** On a run-11-sized tool (a report generator with a contract, a suite and a README bullet) the graph route cost 16× the direct route's subagent tokens (2.41M vs 0.15M), delivered a partial record (its own element-grain test review failed three times), and left 1 post-hoc defect against the direct route's 4; the direct route passed five of six acceptance checks at first delivery and failed the sixth on two small suite defects. The decision rule in the design said this outcome leaves the guidance standing. Read the caveats in the Run 12 entry of [CALIBRATION-LOG.md](CALIBRATION-LOG.md) before citing the numbers: it is one pair, most of the cost sat in one node whose review check had no bounded element set (fixed in prompt v3.5.1), and the direct route's four defects are the kind one bounded review pass catches. A second pair on a different task is planned before this guidance's threshold moves either way.

## More

- [CALIBRATION-LOG.md](CALIBRATION-LOG.md): the decisions and results behind each prompt version. It is the author's own runs, not an independent evaluation. In its run 12 entry the graph route measured once at 16 times the subagent tokens of a direct build, on one pair of runs.
- [TEST-MATRIX.md](TEST-MATRIX.md): the conditions the calibration apparatus has covered, partly covered and never covered.
- [ATTRIBUTION.md](ATTRIBUTION.md): where the graph prompt came from, and the prior art the authoring guide cites.
- [LICENSE](LICENSE): MIT.
- Changelogs: [graph-prompt](plugins/graph-prompt/CHANGELOG.md), [prompt-authoring](plugins/prompt-authoring/CHANGELOG.md).
- [compat/codex/](compat/codex/): an adapter for running the graph prompt under Codex.
