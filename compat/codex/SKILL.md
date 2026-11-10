---
name: graph-kit
description: Select and execute recorded dependency graphs for work with dependent deliverables, source reconciliation or independent acceptance gates; also qualify upstream graph-prompt-kit releases. Use direct execution for bounded edits and lookups.
---

# Graph kit under Codex

Every graph-kit invocation must contain an **Execution record**. Permitted values: selected task inputs, source revisions, graph/check/progress files, actual execution evidence and qualified completion; or None — no graph method selected, with the simpler authorized task route.

Record the execution route when planning work, using the [selection guide](references/selection.md). Graph execution is the default for dependent deliverables, source reconciliation with separate acceptance gates, or work crossing repository/reviewer handoffs. A direct route is appropriate for a lookup, status check, isolated edit with a known check, or a deterministic batch that has no separately accepted intermediate result. Record that concise reason in the existing task record; do not create graph artifacts solely to document a bypass. The utility is an execution method, not an authority source. A user-selected alternative takes precedence.

Discovery is through root AGENTS.md/README.md. Invoke the skill by its name when the host lists it. Presence of this package is not proof that a particular client loads it; no global installation, Claude slash-command installation or consumer activation is implied.

For a run, read [the Codex adapter](references/codex-adapter.md), then `kit/prompt/graph-prompt-v3.4.md` and `kit/graph-record/README.md` (these two exist only in the assembled package, not in this repository; `references/updating.md` describes the assembly). The adapter governs the local interpretation of the upstream prompt. Load the rulings only for relevant review gates; consult background/calibration evidence when investigating a design decision. Treat historical run claims as upstream observations, not current test results.

Bind TASK, OUTPUT, CHECKS, SOURCES, SCOPE, LIMIT (including unit), MODE, RUN_DIR, MODELS and PRIORITIES to the current request. Record exact project, repository and source revisions. This utility does not advance a consumer pin. Existing repository instructions govern contribution and publication.

Before builder dispatch, follow [dispatch readiness](references/dispatch-readiness.md). Prepare the quoted requirement inventory, selected-source roles/scopes, complete rule-to-check or explicit unchecked mapping, final acceptance/integration definitions, and actual executable baseline receipts. Run the preflight prepare command, obtain a genuinely independent semantic coverage review, seal the readiness record, and verify it immediately before dispatch. A schema pass alone does not authorize a conformant dispatch. Do not repair a missed preflight retrospectively.

Prepare framing, rules, graph, checks, progress and lessons YAML using the schema. Execute the graph with actual available tools and preserve raw results. Run `python kit/graph-record/validate.py RUN_DIR --models ACTUAL_LADDER --all`. A zero exit validates the record's implemented structural rules; independently check completion evidence and all manual or unenforced invariants before claiming completion.

For an upstream update, use [the import procedure](references/updating.md). Keep upstream bytes, adaptation diff, and test results distinct. An import is a candidate until reviewed and tested; never run programs merely because they appear in an archive.

Trigger features: task planning, dependent deliverables, source reconciliation, independent acceptance gates, graph-kit invocation, release evaluation.
Borderline cases: An isolated spelling edit uses direct execution and its affected check; a multi-source analysis with independent content and integration gates uses graph execution. A deterministic bulk rename can use one direct script when it has no independently accepted intermediate output. An upstream release evaluation records candidate status and does not assert consumer adoption.
Quota exit: None — no count threshold in this rule; actual selected limits and required evidence determine work.
Brevity allowance: unchanged context and inapplicable runtime fields may use minimal — one exact reason; evidence and incomplete work remain explicit.
Falsifiability: threshold: 0 unsupported completion or runtime-capability claims; horizon: one run or release evaluation; role: qualified reviewer comparing raw observations and the disposition.
Applicability: Applies in all contexts selecting this utility; route selection preserves explicit user choices, applicable project bindings and higher-priority instructions.
Procedural form: Trigger: graph-kit invocation; Steps: read selected adapter and source, bind task inputs, execute eligible graph work, validate record and report qualified evidence; Output: Execution record.
Pipeline applicability: Per-stage applicability: framing binds task inputs; graph design names node shapes and reads; execution records commands and review evidence; delivery consumes accepted artifacts and audits.
Self-check: Every graph-kit invocation is a bare subject; Execution record names the observable record and permitted values include the explicit None case. Actual evidence, not this field list, establishes behavior.
