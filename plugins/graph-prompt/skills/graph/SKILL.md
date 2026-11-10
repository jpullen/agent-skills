---
name: graph
description: Run a multi-step deliverable as a bounded-node graph with gated reviews and a validated run record that another session can resume. Use when the work has dependent outputs that must be accepted before others build on them.
when_to_use: Trigger phrases - "run this as a graph", "/graph-prompt:graph". Also a task with dependent outputs that must be accepted before others build on them, or a handoff that someone must be able to resume from a record.
disable-model-invocation: true
argument-hint: "<task to run as a graph>"
---

# Graph prompt v3.5.1

References for the prompt below:

- "The schema" means `${CLAUDE_SKILL_DIR}/references/graph-record.schema.json`.
- `validate.py`, `coverage.py` and `report.py` are the graph-record skill's scripts. Run each as `python3 ${CLAUDE_SKILL_DIR}/../graph-record/scripts/<name>.py`.
- The background (the rationale for each rule) is `${CLAUDE_SKILL_DIR}/references/graph-prompt-background-v3.5.1.md`. The rulings are `${CLAUDE_SKILL_DIR}/references/graph-prompt-rulings.md`.
- `{{TASK}}` and the other `{{...}}` inputs are the values the person supplies for this run.


```xml
<prompt>
<goal>
Complete {{TASK}} as a graph of bounded nodes, not one long session. Leave a usable {{OUTPUT}} and a run record per the schema that another session can resume, rerun, or extend. The run is complete only when every node's gate passed, the merged {{OUTPUT}} passed {{CHECKS}}, every rule derived from {{SOURCES}} is checked or listed as unchecked, and `validate.py` exits 0 on the record; otherwise it is partial and is reported as partial.
</goal>

<inputs>
Task: {{TASK}}
Deliverable and output path: {{OUTPUT}}
Acceptance checks: {{CHECKS}} — each is a command with an expected exit code and output, or a file property a reader can open and confirm; each has an id.
Source material: {{SOURCES}}
Allowed changes: {{SCOPE}} — the paths that may be written. {{RUN_DIR}} is always in scope.
Run limit: {{LIMIT}} — with its unit per the schema. Node runs are subagent, reviewer, audit, and code runs; lead work before dispatch is reported, not counted. The last ceil({{LIMIT}}/10) runs are a reserve inside {{LIMIT}}: once consumed runs reach {{LIMIT}} minus the reserve, nothing starts except one-item correction returns, each node's full re-gate (a void's rerun included), the integration node (first run or rerun), and re-gates the audits require; each such run is recorded in the reserve list by its kind. The two audits run before every delivery: they are counted, they are recorded in the reserve list, and they are the only runs that may take the count past {{LIMIT}} — a delivery without them is not a delivery. At {{LIMIT}} with a correction or re-gate outstanding, interactive mode asks the person to raise {{LIMIT}} before delivering partial; autonomous mode delivers partial. A raised {{LIMIT}} re-bases the reserve; the raise decision names the runs spent under the old one.
Run mode: {{MODE}} — `interactive` or `autonomous`.
Run directory: {{RUN_DIR}} — default `.graph/<date>-<task-slug>/`. A new run creates its directory and stops if it already exists; a resumed run writes only to its own directory, and only when {{OUTPUT}}, {{SOURCES}}, and the inputs record are unchanged since its last record — any change makes it a new run. Another run's directory is never written to.
Model tiers: {{MODELS}} — cheapest first. The lead runs on the most capable tier. Applies in all contexts.
Priorities: {{PRIORITIES}} — an ordered list of what wins when a check is satisfiable more than one way, or none. Carried into every judgment-node brief and the integration node.

Authority. {{CHECKS}} are necessary, not sufficient. Every specification named in {{SOURCES}} is binding on the deliverable, and so is every fact the person states as an input; both enter rules.yaml at derivation, and a claim resting on either cites it and says no more than it says. A conflict among any two of a check, a specification, an input fact, and a source file is a blocker: it is reported, never designed around, and no check is written to accommodate it. Applies in all contexts.

Before any node runs, write {{RUN_DIR}}/framing.yaml per the schema. Interactive mode: ask the one unknown with `changes_outcome: true` and the largest consequence; every other unknown is assumed. Autonomous mode: every unknown is assumed; an irreversible step that depends on a `changes_outcome: true` unknown is blocked. Every risk is guarded by a named gate or explicitly accepted with a reason.
</inputs>

<role>
Act as the lead that designs, runs, and maintains this graph. Read CLAUDE.md, README, and contributing notes, and inspect the current state before editing. The lead plans, gates, merges, and records; subagents build. Separation of duties: no agent, the lead included, grades an artifact it built. Applies in all contexts.
</role>

<principles>
- Baseline before change: before any node writes, run every `exec` check and every {{CHECKS}} item against the current state and record each result as that row's red evidence. A gate is valid when at least one of its cases is red at baseline; green cases within a valid gate are kept. A gate with no red case is rewritten, or its node dropped, before any node runs.
- Tooling before baseline: every `exec` command names its root or runs from {{OUTPUT}}'s directory; the lead reads every program carried from a previous run for a path, file list, or pattern set of that run and corrects it under a decision; a fresh subagent is asked once, per `partial` filter, what its patterns would miss, and the answer is a decision that names what the filter's residue reviewer is told to look for.
- One node, one scope, one fixed check. A check is written before its node runs and changes only under layer_6_return_paths.
- One change per node run. Every attempt, failed or accepted, is a row.
- One node is a valid graph.
</principles>

<sizing>
A node is split from its neighbor only for a reason the schema's `split_reason` admits: its inputs differ, it can run in parallel, it needs its own gate for one of the four listed conditions and guards a named risk, or one session could not hold it. A node with no such reason is merged into its neighbor. A node whose spec copies a value from another node's output — a count, a list, a name — names that node in `reads`; two nodes that copy from each other are merged or read a third; a copy found after approval gets its edge and a re-gate under a decision.
</sizing>

<layer_1_split>
Break {{TASK}} into a DAG before any work starts; write graph.yaml per the schema. Rules the schema cannot hold and the lead applies while designing:
- The tier rule: start at the lowest tier; move up one for each schema-listed line that is true; cap at the top. Record the fired lines. The reviewer's tier is never below the builder's.
- A node whose rules cannot be written down is a judgment node. Gate type is decided per check, not per node, as `exec_available` per the schema: a check whose `fails_when` verdict a program can return is `exec` on any node; a program that only flags candidates is `partial`, and its flagged list is adjudicated by a `review` gate whose artifact, mutant, and row the schema defines. A check whose fail would be fixed by a token (a tag, a name, a count) rather than a thought is `exec` or `partial`, never `review`.
- For a node whose output is code, the lead writes the gate test, or accepts one the builder proposes, before that builder is dispatched.
- A program that is run machinery lives in {{RUN_DIR}}/code/; a program that is the deliverable lives in {{OUTPUT}}.
Approval: `validate.py {{RUN_DIR}} --models {{MODELS}}` exits 0 on the record as it stands (every node's attempt-1 row present with `not_run` values). Interactive mode: pause for approval. Autonomous mode: record the default approval and continue.
</layer_1_split>

<layer_2_nodes>
Every judgment node runs as its own subagent. Every builder brief contains exactly, in this order: a one-line role (`You build <purpose>. You do not evaluate it.`); the node's spec from graph.yaml; the input paths its `reads` names and nothing else from other nodes; {{SCOPE}} as it applies; the conventions its `needs` names; {{PRIORITIES}}; the check, with the gate test file for a code output; a `Sequestered:` line naming what is withheld (other nodes' outputs not in `reads`, prior-run outputs, any existing implementation of this node's output in {{SOURCES}}, and, for a non-code output or a rule-encoded script's output gate, the gate's program — the builder may run the gate's command and may not open its source; the brief states the format the gate reads) or stating nothing is; a may-not list (write outside `writes`; edit the run record, any gate test, or any file in {{SOURCES}}; open a sequestered gate program); and the stop rule: `If the check cannot pass on an artifact that is correct against the specification, say so and stop. Do not edit inputs, the check, or the specification.`
The builder saves the artifact with every `shape` section present and labeled, may run the check against the saved file, and returns: output path; a self-report of at most five lines; raw check output; any tests it wrote. On any attempt after the first it also returns `changed: <one item> → addresses <section>` or `cannot address: <section>; reason <text>`; two or more items in `changed:` is a failed attempt. Every sentence the builder changed after a check listed it, for whatever reason, is listed in a separate `filter_edits:` return field for that attempt, outside the self-report's five lines and the one-item rule; `none` is a claim the self-report must not contradict — the lead rebuilds the list from the two versions and records a decision; a retry brief carries the earlier attempts' lists, and on an attempt after the first every listed edit belongs to the one item `changed:` names, or the attempt is failed; the lead merges the lists and hands the whole to the filter's residue reviewer. The self-report and builder tests are evidence for the gate; the verdict comes from layer_5_gates only.
A builder that returns nothing, partial output, or an error has used one attempt; before the next, a hypothesis entry is recorded per the schema.
</layer_2_nodes>

<layer_3_code_nodes>
Every deterministic step runs as a program, never as a subagent. Applies in all contexts. Two kinds of code node:
- Deterministic: two competent people given the same inputs produce identical output. One gate: `exec` on the command's exit code and output.
  Borderline: a sort whose tie-break the spec does not define is not deterministic; it is rule-encoded with the tie-break written down. A diff of two files is deterministic.
- Rule-encoded: the program applies written rules to work a person would otherwise judge — extraction by pattern, classification by rule, generation from a template. Two gates: `exec` on the script's own gate test, and `inspect` or `review` on the script's output. Both must pass.
  Borderline: a regex that pulls dates from a log is rule-encoded. A script that decides which of two paragraphs is clearer is not a code node; the rules cannot be written.
A merge is structural (code, deterministic) when no two inputs write the same section; it is content (judgment node, own gate) when any input conflicts, is reworded, or is selected.
  Borderline: two files that each append to the same list is content. Two files that fill disjoint sections of one template is structural.
A required tool that is unavailable is an open issue of kind `blocker` with every alternative tried. Every blocker, this one and the authority rule's: interactive mode asks the person; autonomous mode blocks the nodes it affects and their dependents, and every other node runs.
</layer_3_code_nodes>

<layer_4_permissions>
Publishing, sending, spending, deleting, force-pushing, and any irreversible step: interactive mode asks first; autonomous mode records it as blocked and continues. Applies in all contexts.
Before a merge that touches an existing file, a recoverable copy exists (commit, stash, or {{RUN_DIR}}/backup/).
Enforcement check, before the first node runs: read the active permission configuration and any sandbox flag; compare each rule to {{SCOPE}}; record the result per the schema, with the config path when tooling enforces it. Under `instruction_only` in autonomous mode, every write to a path not listed verbatim in {{SCOPE}} is blocked.
</layer_4_permissions>

<layer_5_gates>
Every edge has a gate, the edge into the final merge included. Every gate opens on evidence of one of three types and never on a confidence statement. Applies in all contexts.
- `exec`: the command, its expected exit code as a number, its actual exit code, and an output excerpt.
- `inspect`: a property the lead confirms by opening the saved file, with path and location.
- `review`: a reviewer subagent, in a fresh context, receives exactly: a one-line role (`You evaluate <purpose> against its check. You do not fix it.`); the node's spec; the check, with the self-agreement statement, every ruling that applies, and each list section named by rule; the input paths the node's `reads` names, read for the passages the artifact cites; the real artifact and its mutant; for a `partial` check, the filter's flagged list, the builder's `filter_edits:`, and the decision naming what the filter would miss; {{PRIORITIES}}; a `Sequestered:` line withholding the builder's self-report, reasoning, and tests. The check may be restated as steps that add no property; a fail resting on a property not in `fails_when` voids the review as a surviving mutant does, and the steps are revised as a check revision before the rerun. Every review check carries one standing property, agreement with itself, counted as in `fails_when` and open to a mutant: a count, list, label, or cross-reference anywhere in the artifact — not only in the sets the check names — that contradicts the artifact or a file in `reads` fails its section (cause (a) on retry), and the brief says so as a verdict rule: a contradiction of that kind the reviewer can quote is a fail, never a borderline, and the return has no third value; when the quoted value in `reads` is the wrong one, the hypothesis records cause (b). An `observations:` entry that quotes such a contradiction is that fail: the lead records the section as failed, and the reviewer's pass on it does not stand. An interpretation the lead adds to a brief — of an input fact, a check term, or a source — is a decision of kind `ruling` recorded before dispatch; a fail resting on a ruling that the text of any artifact accepted before that verdict contradicts is void, counts toward escalation, and the ruling is revised, never the artifact. The reviewer's return may add `observations:` outside the check, which are not proposed fixes and never change the verdict; on a passing gate the lead triages each into a check revision that re-gates the node, an open issue, or nothing, each as a decision. It returns a verdict per `shape` section with cited evidence; where a section is a list of like elements (table cells, rows, participants), the brief names the set by rule (`every cell of the scoring table`) and the verdict covers every element; a verdict covering fewer is void. A check that fails when a behaviour is removed names the element set it covers — an enumerated list per clause, or the lead's mutant list — bounded to what the artifact's output, exit code, or files make observable; an element the reviewer adds outside that set is an observation. For a test suite, a parametrized test's cases are one test, and two tests share a failure reason only when they name one element. The node fails if any section fails. Every section `fail` carries at least one verbatim excerpt that appears in the artifact; a fail without one is void. A return containing a proposed fix or alternative is void. The reviewer's tier is never below the builder's; the builder is never the reviewer.
Discriminating evidence:
- `exec`: the baseline run is the red result, and red is an assertion failure. A crash, import error, missing symbol, or missing path is not red; the lead stubs the minimum needed to reach the assertion and records the stub path.
  Borderline: a TypeError inside the assertion is not red. An assertion that fails on empty output is red.
- `inspect`: the `fails_when` line is the discriminating evidence; no runtime step.
- `review`: the reviewer receives the real artifact and one mutant, unlabeled, in random order. The mutant removes exactly one property named in the check's `fails_when`; it is the baseline state when one exists. The label draw is written under {{RUN_DIR}}, never beside the variants or in any path the reviewer reads. The gate opens when the reviewer fails the mutant and passes the real artifact. If the mutant survives, the review is void: recorded, counted against {{LIMIT}}, not counted as a correction attempt; the check is tightened or the reviewer brief replaced before a rerun. A second void on the same gate is `escalated`.
A gate shows that a check was able to fail and then passed. The word `proven` appears in no authored record content or comments. Literal source scalar content in rules.yaml's rules[*].quote is exempt; preserve exact attribution without treating it as endorsement, approval or a passing check.
Verdicts, their meanings, their next actions, and what each records are per the schema.
</layer_5_gates>

<layer_6_return_paths>
Correction edge. Entry: a gate returns `fail`. Body: the unit returns to the node that produced it with the reason, the evidence, and the scope `fix this node only`; before each retry a hypothesis entry is recorded with one cause:
  (a) builder error — retry on the same tier; a second (a) on the same node retries one tier up, capped at the top, the reviewer raised to match and the move counted in the node's model
  (b) upstream field wrong — this node fails; the upstream node named in `reads` for that field reopens
  (c) check wrong — the lead revises the check and records was / now / reason; a revised check is never weaker than what {{CHECKS}} or a {{SOURCES}} specification requires; a check in graph.yaml that differs from its row with no such decision voids the gate. A check that traces every hunk to a named cause admits, by construction, a sentence a later gate returned to the node, bounded to that sentence's citations and scope words; the return decision names the sentence and no check revision is needed
  (d) source defect — the artifact is correct against the specification and the gate fails because a file in {{SOURCES}} violates it: no retry; an open issue of kind `source_defect` per the schema, handled as a blocker
The retry's `changed:` names the failed section it addresses. A `cannot address:` return triggers cause (c) triage; if the lead upholds the check, the next verdict on that section is the second fail.
Exit: the gate passes; or the third attempt fails and the node is marked failed with every dependent blocked and every independent node continuing; or, on a `review` gate only, the same section fails twice with the builder's last return `cannot address` and the verdict is `dissent` — the artifact is accepted for dependents, both positions are recorded, and the run cannot complete as other than partial; or cause (d) blocks until the person decides.
A correction that changes any file the integration node reads reruns the integration node from its first item.
Learning edge: every accepted result adds a lessons entry per the schema. One run is an observation. An entry is promoted to a template default when it is a hard constraint of the environment or has held in two or more runs.
</layer_6_return_paths>

<layer_7_completion>
Before execution: derive rules.yaml from every specification named in {{SOURCES}} and every input fact, one entry per rule the specification states about the deliverable, with its quote; give every {{CHECKS}} item a row naming the rules it exercises or none; list every rule with no exercising check in the record as unchecked, with its reason, per the schema, before approval, and report the list at delivery. The run may complete with unchecked rules; it may not complete with a rule that a check contradicts.
A final integration node runs {{CHECKS}} against the merged {{OUTPUT}}. It writes raw results to {{RUN_DIR}}/integration.out; only the lead writes rows. Each review-type item has its own row and its own mutant. A residue review over a set of files is briefed to read every file in full and to return a per-file ledger; a verdict reached by diffing the two sets or by pattern search covers fewer sentences than the set and is void. A review-gated artifact whose sha256 at integration equals its sha256 at its node gate carries that gate's verdict; otherwise a fresh review runs.
Two audits run after the integration node and before every delivery, partial included:
1. Record well-formedness: `validate.py {{RUN_DIR}} --models {{MODELS}}` exits 0. A non-zero exit names the first failing rule; the lead corrects the record, never a verdict, and reruns. Rules in rules.yaml that concern the record itself are prose; the validator counts them and the lead checks them by hand, recording which.
2. Evidence audit: a fresh subagent receives exactly a one-line role (`You verify evidence citations. You do not know who wrote them or what the task was.`), the newest `pass` row per subject of type `exec` or `inspect` verbatim (a superseded attempt's row has no artifact to rerun against), and read access to {{RUN_DIR}} and {{SCOPE}}; every cited command carries absolute paths. For each row it returns `confirmed`, `miscited`, or `unfound`, plus `notes:` for anything outside its rows. At or below 10% miscited-or-unfound the audit passes and each miscited or unfound row reverts to `unresolved`; above 10% it fails and every `inspect` row reverts to `unresolved` for re-gating. Notes are recorded and never change a verdict. A degraded evidence audit makes the run partial.
Definition of Done: every node output exists at its recorded path and opens; every gate ran against the saved version and has a row with red evidence; the integration node passed; both audits passed, the evidence audit in a fresh context; no row is `dissent`, `unresolved`, or `escalated`; no rule is contradicted by a check. Anything less is partial, and partial delivery names every node's state and what would resolve it.
</layer_7_completion>

<execution_loop>
Entry: graph.yaml approved; framing.yaml and rules.yaml written; enforcement recorded; baseline rows present.
Body: read the record and select nodes whose every upstream is accepted at its newest attempt — a node returned after a correction, or whose upstream was, is re-gated only after that upstream is re-accepted; run independent nodes in parallel, a code node running its gate test first (red confirmed), then its script, then its gate; gate every output before any node reads it; return failed units through the correction edge, never rerunning accepted ones; merge accepted outputs, structural in code and content in a gated judgment node; after every terminal state, update progress.yaml; when no node is ready and none is running, run the integration node and then the two audits.
Exit: completion; a critical-path blocker; an `escalated` node on the critical path; a cause (d) block in autonomous mode; {{LIMIT}} minus the reserve for ordinary work; or {{LIMIT}} for everything but the two audits. Every subagent, reviewer, void review, audit, and code run counts against {{LIMIT}} when it happens.
</execution_loop>

<handoff>
progress.yaml per the schema is the handoff. Resumption: read the record; continue from `next_action`; accepted nodes are not rerun. Override: {{SOURCES}} differ from the recorded run — new {{RUN_DIR}}, a `sources_changed` decision naming them, and every node whose `reads` include a changed source re-gated against its saved artifact before it is carried.
</handoff>

<delivery>
Return {{OUTPUT}}, the run record, and every gate test file. State what was checked, what passed with evidence, what failed, what is unresolved, any dissent with both positions, anything escalated, every unchecked rule, every assumption, and both audits, notes first, then counts. Use the schema's verdict vocabulary; never `proven`. State a gap as `no gate fired on <condition>; propose: <check>`, never as an intention. Report usage only as the harness measured it. After review, save the node specs as a template with run paths stripped, and re-scan every layer against any rule added this version, recording findings as decisions.
</delivery>
</prompt>
```
