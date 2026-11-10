# Graph Prompt v3.5.1 — Background

Companion to the v3.5.1 graph prompt, the `<prompt>` block in this skill's SKILL.md (v2.8 had no background file of its own; its single change, format by reference to the schema, is D-S below). Decisions D34–D38 come from run 5 (the repository's `CALIBRATION-LOG.md`, RF-7 to RF-12); D39–D40 from run 6 (RF-13 to RF-17 and the third T-18 inventory); D41–D44 from run 7 (RF-19 to RF-24). The prompt carries obligations; this file carries why each exists, what would show it wrong, and the self-checks the Prompt Authoring Guide (v2.3.0) requires. Nothing here is read at runtime.

Mechanism-claim marker default for this file: `[Hypothesis: first ten runs of v3.1 on real tasks; disconfirmation = the stated threshold is crossed within the stated horizon]`. Claims with their own marker override the default.

---

## 1. Design decisions, each with its disconfirmation

Each decision is stated as the obligation in the prompt, the mechanism it assumes, and the three falsifiability tokens (threshold, horizon, role) per RULE-010.

### D1 — No agent grades an artifact it built (`role`, `layer_2`, `layer_5`)
`[Hypothesis: a builder evaluating its own artifact passes defective artifacts at a materially higher rate than an independent evaluator — disconfirmation: builder-graded and independently-graded gates show equal defect-escape rates]`
Falsifiability: threshold: ≥1 artifact that passed a builder self-check and failed the independent gate; horizon: 20 gates; role: lead reading checks.md.

### D2 — Integration gate against `{{CHECKS}}` (`layer_7`)
`[Hypothesis: all node-local gates passing does not entail the merged output passing acceptance — disconfirmation: no run in which every node gate passed and the integration gate failed]`
Falsifiability: threshold: ≥1 such run; horizon: 10 runs; role: lead.

### D3 — Run mode with autonomous defaults (`inputs`, `layer_1`, `layer_4`)
`[Hypothesis: without a declared mode, unattended runs stall at the first question or approval pause — disconfirmation: unattended runs of v1 complete at the same rate as v2.5 autonomous runs]`
Falsifiability: threshold: >0 stalls per 5 unattended runs; horizon: 5 runs; role: person resuming the session.

### D4 — Every check names when it fails; `exec` red at baseline (`layer_1`, `principles`, `layer_5`)
`[Hypothesis: checks authored without a failing state are green at baseline at a material rate — disconfirmation: <10% of checks green at baseline across the first 5 runs when the fails-when line is omitted]`
Falsifiability: threshold: >10% baseline-green; horizon: 5 runs; role: lead reading `red evidence` column.

### D5 — Reviewer tier never below builder tier (`layer_1`, `layer_5`, `layer_6`)
`[Hypothesis: a reviewer less capable than the builder passes both the real and the deficient variant at a higher rate — disconfirmation: void-review rate is independent of the reviewer/builder tier gap]`
Falsifiability: threshold: void rate >10% when reviewer < builder; horizon: 20 review gates; role: lead reading void records in checks.md.

### D6 — Builder-written tests are evidence, not the gate (`layer_2`)
`[Hypothesis: a test and an implementation written by the same agent agree with each other when both are wrong — disconfirmation: builder-written tests catch the same defects as lead-written gate tests across 20 code nodes]`
Falsifiability: threshold: ≥1 code node where builder tests passed and the lead's gate test failed; horizon: 20 code nodes; role: lead.

### D7 — Red is an assertion failure, not a crash (`layer_5`)
`[Hypothesis: a crash-red (import error, missing symbol) is satisfied by any change that makes the test run, including a wrong one — disconfirmation: no gate opened on crash-red whose artifact later failed inspect/review]`
Falsifiability: threshold: ≥1 such gate; horizon: 20 exec gates; role: lead.

### D8 — Deficient variant with one named property removed (`layer_5`)
`[Hypothesis: a reviewer that cannot fail a one-property-removed variant cannot discriminate on that property in the real artifact — disconfirmation: reviewers that passed the variant still catch that property's absence in real artifacts]`
Falsifiability: threshold: ≥1 void review whose reviewer later failed a real artifact on the same property; horizon: 20 review gates; role: lead.
Design note: `removed:` is restricted to a property named in the `fails when` line. This is the observable rewrite of v2.3's "not an absurd mutation"; the variant is now checkable against the spec rather than against the lead's taste.

### D9 — One run is an observation; promote at two (`layer_6`)
`[Hypothesis: a rule written from one accepted result generalizes wrongly to the next run at a material rate — disconfirmation: single-run rules promoted immediately hold on the next run as often as two-run rules]`
Falsifiability: threshold: ≥1 promoted single-run rule contradicted on the next run; horizon: 10 runs; role: person reviewing lessons.md.

### D10 — Cost pressure never changes a check (`execution_loop`, `layer_1 because:`)
`[Hypothesis: under a visible run limit, a lead with model and gate choices will cheapen the gate before cheapening the builder unless the gate is declared fixed — disconfirmation: no check revision under cost pressure in 10 runs without the rule]`
Falsifiability: threshold: ≥1 check revision whose Decisions reason names cost; horizon: 10 runs; role: lead reading Decisions.

### D11 — Named-field edges (`layer_1 reads:`, `layer_6 cause b`)
`[Hypothesis: edges that name only the upstream node cause triage to misattribute upstream failures to builder error — disconfirmation: cause (b) is selected at the same rate and with the same accuracy under node-only edges]`
Falsifiability: threshold: ≥1 cause (b) that identifies a field node-only edges would not have named; horizon: 10 correction events; role: lead.

### D12 — Sequestered line in briefs (`layer_2`)
Inherited from the Prompt Authoring Guide RULE-P02: `[Hypothesis: visibility of a candidate during generation produces convergence on that candidate even when instructed to ignore it]`. Applied here to a builder seeing an existing implementation of its own output.
Falsifiability: threshold: ≥1 builder output that reproduces a sequestered implementation's defect; horizon: 20 builder runs; role: reviewer.

### D13 — Two-file split (this file's existence)
`[Hypothesis: rationale inline in an execution prompt is read every run and acted on in none, costing tokens and diluting the obligations — disconfirmation: a run on v2.3 and a run on v2.4 show equal obligation-compliance and equal prompt-token cost]`
Falsifiability: threshold: v2.4 prompt ≥15% shorter with no obligation dropped (measured once, at authoring); horizon: this version; role: author.
**Measured at authoring: v2.3 prompt 2,572 words → v2.4 prompt 2,457 words, 4.5% shorter.** The threshold was not met. Rationale removal (~12 clauses) was offset by RULE-001 field conversions, RULE-002 borderline pairs, RULE-012 applicability lines, and the enumerated brief. The size half of this hypothesis is disconfirmed; the compliance half is untested. Revised claim: the split relocates rationale without shrinking the prompt, and its value, if any, is in obligation density, not token count. `[Hypothesis: obligation-compliance per run is higher under v2.4 than v2.3 — disconfirmation: equal rates of missing required fields in graph.md across 10 runs each]`

### D14 — Producer-side `shape:` with name-match before approval (`layer_1`)
Source: Prompt Authoring Guide Part 1, "Required output shape" + RULE-P01 name-matching. v2.4 adopted the consumer half (`reads:` names fields) without the producer half, so a `reads:` field could name a section no upstream node declared.
`[Hypothesis: edges verified by name-match between declared shape and declared reads catch missing-section failures before any node runs that would otherwise surface as cause (b) during correction — disconfirmation: no name-match block at approval across 10 runs, or the blocks it raises never correspond to a later cause (b)]`
Falsifiability: threshold: ≥1 approval block that names a section a downstream node would have read; horizon: 10 runs; role: lead reading Decisions.

### D15 — Tier rule on spec properties (`layer_1`)
Source: Guide Part 1 control levers ("opus when Stage 2 returns ≥5 domains"). Replaces v2.4's `because:` clause, which was the lead's judgment, with counted triggers on the node spec. Thresholds are the first-run defaults; lessons.md promotion may revise one at a time with was / now / reason.
`[Hypothesis: counted triggers assign tiers at least as well as the lead's per-node judgment and remove the cost-shaped reasoning the `because:` rejection clause had to police — disconfirmation: cause (d) escalations are more frequent under the tier rule than under v2.4 `because:` across 20 judgment nodes]`
Falsifiability: threshold: cause (d) rate under the tier rule > rate under `because:`; horizon: 20 judgment nodes; role: lead reading lessons.md `tier rule:` lines.

### D16 — `changed: <one item>` on retry (`layer_2`)
Source: Guide Stage 6 output shape, `Improvements made` slot. The principle "one change per node run" had no format rule in v2.4.
`[Hypothesis: a builder required to name its one change makes one change; a builder not required makes several, and a gate that then passes cannot attribute the pass — disconfirmation: retries under v2.4 (no `changed:`) show the same single-diff rate as under v2.5]`
Falsifiability: threshold: ≥1 v2.5 retry rejected for a two-item `changed:`; horizon: 10 retries; role: lead.

### D17 — Role line, `does:` mapped to `shape:`, and reviewer output per section (`layer_2`, `layer_5`)
Source: Guide Stage structure (one-line role, TASK as ≤4 imperatives, required output shape). Three design elements applied together: the builder and reviewer each get a one-line identity stating what they do and do not do; the builder's task is enumerated imperatives each producing a named section; the reviewer verdicts per section rather than holistically.
`[Hypothesis: per-section review verdicts locate failures more precisely than a holistic pass/fail, so correction-edge scope "fix this node only" narrows to the failed section — disconfirmation: builders on retry change sections the reviewer passed at the same rate as under holistic verdicts]`
Falsifiability: threshold: ≥1 retry whose `changed:` names a section the reviewer passed; horizon: 10 retries; role: lead.

Deliberate non-adoption: Guide Stage 5 produces `Alternatives`. The reviewer here returns no fix and no alternative, and a return containing one is void. In the Guide's pipeline, critique runs once and refinement is a separate stage; here the reviewer re-reviews the retry, so a reviewer that supplied the fix would grade its own suggestion — D1 through the back door.

### D18 — `{{PRIORITIES}}` as a separate input (`inputs`, `layer_2`, `layer_5`, `layer_7`)
Source: Guide Stage 3 PRIORITIES block, distinct from TASK. v2.4 had no shared tiebreak when a check is satisfiable several ways or two `{{CHECKS}}` items conflict.
`[Hypothesis: without a declared priority order, builder and reviewer resolve a satisfiable-several-ways check differently, and the disagreement surfaces as a cause (a) retry that no builder change can fix — disconfirmation: no correction event in 10 runs whose reviewer fail cites a property the builder could defend under a different priority order]`
Falsifiability: threshold: ≥1 Decisions entry recording an integration-node conflict resolved by `{{PRIORITIES}}`; horizon: 10 runs; role: lead.

### D19 — Risks in framing.md, cited by `own gate` (`inputs`, `sizing`)
Source: Guide lightweight variant question 4 ("What could go wrong?"). Gives every `own gate` split a stated provenance and gives every stated risk either a guard or an explicit acceptance.
`[Hypothesis: gates placed against a named risk are retained under cost pressure more often than gates placed by instinct — disconfirmation: `own gate` nodes are merged away at the same rate with and without a `risk` citation]`
Falsifiability: threshold: ≥1 Risks entry with `guarded by: None — accepted` that later appears as a failure; horizon: 10 runs; role: person reviewing framing.md against the delivery block.

### D20 — Evidence audit in a fresh context (`layer_7`)
Source: PIPELINE-001 Stage 2b.1 (independent citation verification: rows verbatim, author sequestered, numeric threshold). In v2.5 the lead wrote every `inspect` verdict and its evidence, and nothing graded those — D1's rule had a gap at the lead.
`[Hypothesis: an independent verifier given only checks.md rows finds miscited or unfound evidence at a non-zero rate in lead-written inspect rows — disconfirmation: zero miscited/unfound across 50 audited rows]`
Falsifiability: threshold: ≥1 miscited or unfound row; horizon: 50 audited rows; role: the audit subagent, recorded in progress.md Audits.
Threshold choice: 10%, stricter than 2b.1's 30%, because every audited row is a gate the run claims opened on evidence; a convergence map tolerates looser matching.

### D21 — `Isolation:` with a degraded mode (`layer_5`, `layer_7`)
Source: PIPELINE-001 execution-context declarations (`Isolated subagent — fresh context` / `Sequential same-context — degraded execution; verdict advisory`) and sub-check 7e (declared context matches deployment). Same shape as layer_4's `Enforcement:`.
`[Hypothesis: without a declared isolation value, a harness that cannot spawn a subagent degrades review into lead self-review silently — disconfirmation: no `same context — degraded` row ever appears across 10 runs on a subagent-capable harness, and on a chat harness every review row is correctly marked degraded]`
Falsifiability: threshold: ≥1 review row on a non-subagent harness marked `fresh subagent`; horizon: 10 runs; role: well-formedness script (isolation line).

### D22 — Verbatim anchors on reviewer fails (`layer_5`)
Source: PIPELINE-001 Stage 5 ("quote verbatim excerpts … do not generate critique that invents content"). Adopted as ≥1, not ≥3: the Guide's RULE-007 requires a count rule to carry a `None at threshold` exit, and small artifacts cannot yield three distinct excerpts; one excerpt that must appear in the artifact is the grep-able minimum.
`[Hypothesis: reviewer fails without a required excerpt include fails about content not in the artifact — disconfirmation: zero voided fails for a missing or non-matching excerpt across 30 review gates]`
Falsifiability: threshold: ≥1 void for a non-matching excerpt; horizon: 30 review gates; role: lead.

### D23 — Rerun the integration node from its first item after any correction (`layer_6`, `layer_7`)
Source: PIPELINE-001 Stage 7 ("re-run Stage 7 from sub-check 7a"). v2.5 did not say whether a correction re-ran all of `{{CHECKS}}`.
`[Hypothesis: a correction that fixes one acceptance item can regress another — disconfirmation: no integration rerun fails an item that passed before the correction, across 10 corrections]`
Falsifiability: threshold: ≥1 regressed item; horizon: 10 corrections touching `{{OUTPUT}}`; role: integration node.

### D24 — Record well-formedness as a code node (`layer_7`)
Source: PIPELINE-001 sub-check 7f (verifies the verification table: one row per entry, verdicts from the allowed set, threshold computed). Every line is deterministic, so under layer_3 it is a script, not a condition the lead reads. The script corrects the record, never the verdicts.
`[Hypothesis: a lead reading "complete means" lines misses a missing row or an out-of-set verdict at a non-zero rate; a script does not — disconfirmation: the script never exits non-zero on a record the lead had already declared complete, across 10 runs]`
Falsifiability: threshold: ≥1 non-zero exit on a lead-declared-complete record; horizon: 10 runs; role: the script.

### D25 — Verdict table; `dissent` and `escalated` terminals (`layer_5`, `layer_6`)
Source: PIPELINE-001 verdict table (PASS / CORRECTED / BLOCKED / PRIMARY+DISSENT / ESCALATED with next-action column). `dissent` is scoped to `review` gates only, requires the same section to fail twice and a `cannot address` return, unblocks dependents, and forces the run to `partial`. `escalated` replaces "tighten and retry" on a second void.
Deliberate non-transfer: PIPELINE-001's "no iteration cap." It conflicts with `{{LIMIT}}`; `dissent` provides the exit the pipeline uses the no-cap for.
`[Hypothesis: blocking every dependent after three attempts on a judgment disagreement wastes more of the graph than delivering with the disagreement recorded — disconfirmation: dissent rows are never followed by accepted dependents, across 10 dissents]`
Falsifiability: threshold: ≥1 dissent row with ≥1 accepted dependent; horizon: 10 dissents; role: lead reading progress.md Graph.

### D26 — `changed:` names the failed section; `cannot address:` alternative (`layer_2`, `layer_6`)
Source: PIPELINE-001 Stage 6 ("Improvements made, mapped to Stage 5 critiques"; "where a weakness cannot be addressed, state it as a remaining uncertainty"). The `cannot address` return is the trigger for cause (c) triage and, if the check is upheld, the path to `dissent`.
`[Hypothesis: a builder required to map its change to the failed section stops making unrelated changes on retry — disconfirmation: `changed:` names a section the reviewer passed at the same rate as under v2.5]`
Falsifiability: threshold: ≥1 retry rejected for addressing a passed section; horizon: 10 retries; role: lead.

### D27 — Authority: specifications in {{SOURCES}} bind; conflicts halt (`inputs`)
Source: calibration runs 1–3 (F-09, F-12, F-13). Three leads on one plant: v2.6 blocked at gate, v1 designed around it, v1.1 (v1 + a warning-form authority line) surfaced it and asked. The line in v2.7 is halt-form: a conflict "is reported, it is never designed around, and no check is written to accommodate it."
`[Hypothesis: a halt-form authority rule removes the "design around" outcome entirely; a warn-form rule only makes it visible — disconfirmation: a v2.7 lead given a checks/spec conflict writes a check that accommodates it]`
Falsifiability: threshold: ≥1 accommodating check; horizon: 5 runs with a planted conflict; role: independent conformance auditor.
Measured so far: 0/1 under v2.6 (which had no line; structure alone halted), 1/1 under v1, 0/1 under v1.1-B.

### D28 — rules.md: derive the rule list before execution; checks name what they exercise (`layer_7`)
Source: F-13, F-15, and the independent audit (89 rules derivable from the spec, 12 tested, 5 in the well-formedness audit). The audit as specified in v2.6 was a smoke test. v2.7 makes the derivation a required pre-execution artifact, ties every `{{CHECKS}}` item to the rules it exercises, and lists the remainder as `unchecked` in delivery. The well-formedness script runs against rules.md.
`[Hypothesis: a lead required to list unchecked rules writes more spec-derived checks than one not required to — disconfirmation: the unchecked count under v2.7 equals the count of rules a v2.6 lead left untested on the same task]`
Falsifiability: threshold: unchecked count < 77 of 89 on the template-tooling task; horizon: 1 run; role: lead, verified by auditor.

### D29 — Cause (e): source defect (`layer_6`)
Source: F-05 (run 1 blocked with nowhere to route). The correction edge now has a cause for a correct artifact failing on a defective source, with the unblock options stated in the record.
`[Hypothesis: without cause (e), a lead facing a source defect either stalls or weakens the gate — disconfirmation: v2.6 leads across 5 source-defect runs neither stall nor weaken]`
Measured: 1/1 stalled under v2.6 (correct behavior, but required a human); 1/1 designed around under v1.

### D30 — `not run` states; audits on every delivery; auditor notes (`layer_5`, `layer_7`)
Source: F-06, F-07, O-E. The record format could not represent a gate that had not run without violating its own validator; audits were unspecified on partial delivery; two auditors in a row volunteered observations outside their rows. All three are now representable.
`[Hypothesis: auditor notes carry signal at a rate worth recording — disconfirmation: across 10 audits, no note identifies a defect the rows did not]`

### D31 — Green-at-baseline per gate; integration carries hash-equal verdicts; exact exit codes (`principles`, `layer_7`, `layer_5`)
Source: F-01, F-02/D-04, F-08. Each was a silence the run-1 lead resolved with a recorded decision; v2.7 states the resolution.

### D32 — Nineteen ambiguity rulings (various)
Source: the independent conformance audit. Each ruling is in `graph-prompt-rulings.md` with its location. The test is T-16: a second cold derivation should converge with the first on rule count and wording.
`[Hypothesis: two independent readers of v2.7 derive rule lists that differ by fewer than 5 rules — disconfirmation: a difference of 5 or more]`
Falsifiability: threshold: |n1 − n2| ≥ 5 or ≥ 5 rules with materially different wording; horizon: one derivation pair; role: author comparing the two lists.

### D33 — Vocabulary from prior art (`layer_5`, `role`, `layer_7`, `layer_1`)
Source: prior-art convergence check (rows 1, 2, 10, 11, verified 0% miscited). `deficient variant` → `mutant`, `removed:` → `mutation:`, separation of duties named, Definition of Done named, prerequisites/targets as parentheticals. `accepted` → `succeeded` not adopted (state-vocabulary churn, weak gain).
`[Hypothesis: a lead model behaves more consistently under established terms than under coined ones — disconfirmation: no measurable difference in gate construction across 5 runs]` — low priority; recorded for completeness.

### D-S — Format by reference (v2.8; `preamble`, every layer)
Source: T-16 (two cold derivations of v2.7 prose diverged by a wide margin) and T-19/T-20 (two cold readers of the schema converged; 594 schema-derived mutants all caught). The record's format moved out of the prompt into `graph-record.schema.json` + `validate.py`; the prompt keeps behavior. 4,030 → 2,831 words.
`[Hypothesis: a machine-checked format removes the class of run defects that were format misreadings — disconfirmation: a run-5 or later gate failure traceable to a misread field or value]` — run 5: zero such failures; validate.py caught three lead errors (RF-7) before they reached a gate.

### D34 — Tier lines frozen at dispatch (schema `model.tier_rule`, X25)
Source: RF-8. A node was dispatched at opus under fired tier-rule lines; reclassifying its check to `exec` afterwards left fewer, and the record could only say sonnet or misuse `escalations`. The lines now record what fired at dispatch; a node with a `check_revision` decision is exempt from X25's recomputation.
`[Hypothesis: check revisions after dispatch are rare enough that the exemption never hides a tier error — disconfirmation: a tier that validate.py would have rejected surviving under the exemption in any of the next five runs]`.

### D35 — Phase attribution (schema `decision.phase`, `subagents[].phase`)
Source: RF-9. Integration-phase reviewers and decisions had no node and the schema required one; they were attributed to artifact-owning nodes, which was false. `phase: integration|delivery|audit` replaces `node` for work done outside any node; builders never carry a phase.
Falsifiability: threshold: any subagent or decision in the next five runs that fits neither a node nor a phase; horizon: five runs; role: validator.

### D36 — Exec availability per check, residue path for heuristics (schema `check.exec_available`, `check.residue`, X21/X23/X28; `layer_1`, `layer_5`)
Source: RF-8 and RF-10. `program_considered` lived on the node and was copied verbatim across judgment nodes, informing nothing; a node's check was structural and should have been `exec` from the start. A regex over prose returned hits with no real miss, and the residue needed a reviewer the design had not declared. Now every check states `yes|no|partial`; `partial` names the residue path, and X28 requires a `<id>-residue` review row with its own red evidence whenever the program's exit does not match. `program_considered` is removed — the first field cut since v2.3.
`[Hypothesis: deciding exec availability per check finds at least one program the per-node framing would have called judgment, in each of the next three runs — disconfirmation: a run where every check's exec_available equals what the node kind would have implied]`.

### D37 — The reviewer brief adds no property (`layer_5`)
Source: RF-11. A node's attempt-2 fail came from a method the lead wrote into the reviewer brief that was stricter than the check's `fails_when`; the check itself was right. v2.8 said the brief contains "exactly" five items and the lead added a sixth. The brief may restate `fails_when` as steps that add no property; a fail resting on a property not in `fails_when` voids the review (as a surviving mutant does — one void count), and the steps are revised as a `check_revision` decision before the rerun. Rulings R25–R26. T-24's three cold reads settled the void-versus-attempt question: a void, because the artifact was never shown wrong against the check.
`[Hypothesis: with methods bounded to fails_when, cause (c) from the brief does not recur — disconfirmation: a cause-(c) hypothesis in the next five runs whose was/now names the brief]`.

### D38 — Fan-in tier line: not changed (`layer_1`, schema `tier_rule_line`)
Source: RF-7. `reads_three_or_more_upstream` computed opus for one node's table output. One observation; the learning edge promotes a tier-rule change only when it has held in two runs. Pre-registered as T-22: on the next two runs, for each node where that line fires, record whether the content reconciles its inputs (`content_merge` would also fire) or copies from them; if it only copies in both runs, drop the line.
Falsifiability: threshold: two runs with a fan-in-only node whose first-attempt pass at the computed tier would, by the reviewer's own account, have passed one tier lower; horizon: two runs; role: lead.

### D39 — A pending state for an asked question (schema `unknowns[].disposition`, X29)
Source: RF-13. At the approval pause of run 6 a framing unknown had been put to the person and not answered; the schema allowed only `asked` (answer required) or `assumed`, so the record carried a fake answer. `pending` names the open issue that carries the question and is legal only while `next_action` is blocked on it; the validator (X29) rejects a pending unknown once the run moves on. In state-machine terms: the record now has an explicit *waiting* state instead of overloading *answered*.
Falsifiability: threshold: a record that validates with a pending unknown after its blocker closed; horizon: five runs; role: validator.

### D40 — The first cut: four obligations with no occasion in six runs (`layer_6`, `layer_7`, `principles`)
Source: three T-18 inventories (runs 4, 5, 6). Cause (d) "builder under-capacity" folds into cause (a) as its tier-up form (the schema's `escalations` counter and `under_capacity` hypothesis cause stay; only the separate branch goes). The cost-pressure sentence goes (its one protective clause, "never changes a check", is already the principles' rule that checks change only under layer_6). The `{{PRIORITIES}}` tiebreak between conflicting acceptance items goes; a conflict between two checks joins the authority rule as a blocker, which is stricter (it asks instead of resolving silently) and matches what run 6 showed the derivation step does with a conflict. The threshold-promotion clause goes; promotion of a lessons entry to a template default stays. 2,933 → 2,892 words after the cold reads (F-19): the first version since v2 that is shorter than its predecessor. T-25 is the test: two runs on v3.0, pass if no finding traces to a cut line.
`[Hypothesis: none of the four cut obligations would have fired in the next two runs — disconfirmation: a run-7 or run-8 finding whose fix is to restore one of them]`.

### D41 — Enumerable sections are reviewed element by element (`layer_5`)
Source: RF-19. Two fresh reviewers of one unchanged artifact flagged different elements; a review verdict is a sample with per-element detection probability below one, and a mutant proves only that the reviewer can detect that defect class. Where a `shape` section is a list of like elements, the brief names the set by rule and the verdict covers every element; fewer is void. The re-gate passed once its brief named the whole set by rule.
`[Hypothesis: per-element verdicts on enumerable sections remove the fail-then-new-fail pattern on retries — disconfirmation: a second fresh review of a per-element-passed section finding an element the first passed, in the next three runs]`.

### D42 — Token-fixable checks are never reviews (`layer_1`)
Source: RF-23. Run 7's one integration fail was missing citation tags; the fix cost eight node runs of re-gating for zero change in meaning. A check whose fail is fixed by a token (tag, name, count) is `exec` or `partial`; a reviewer judges only residue. Rulings R36–R37 bound it (per-property, closed vs open candidate sets, the person's `{{CHECKS}}` keep their type).
`[Hypothesis: under D42 no correction cycle in the next three runs spends more than two node runs on a token-class defect — disconfirmation: one that does]`.

### D43 — Input facts are binding and bounded (`inputs`, `layer_7`)
Source: RF-24 and run 7. Facts the person states as inputs worked as a citation class: every planted mis-citation of an input fact was caught. The audit found the mirror error — a premise cited to an input that does not state it. Inputs now enter rules.yaml at derivation, a conflict involving one is a blocker, and a claim resting on one says no more than it says (test in R40).
Falsifiability: threshold: an audit `notes:` entry in the next three runs reporting an input stretched beyond its words on a claim that cites it; horizon: three runs; role: auditor.

### D44 — Audit notes before counts in delivery (`delivery`)
Source: RF-24 and run 5: in both runs the audit's row-level verdict passed and the finding that could change the design lived in `notes:`. Delivery states each audit's notes first, then its counts (R41).
Falsifiability: threshold: a person's post-delivery question that the notes already answered but the delivery buried under counts; horizon: three deliveries; role: author.

### D45 — Prose that restates a schema-required field is cut (`layer_2`, `layer_6`, `layer_5`)
Source: RF-16, RF-20, RF-21: three times the validator caught the lead skipping an obligation on a failure path that the prose also stated. On those paths the prose explains and the schema enforces. Three sentences enumerating fields the schema requires (source-defect issue fields, builder-failure causes, dissent-row content) now say "per the schema". −30 words; v3.1 nets +73 over v3.0 for the four additions.
`[Hypothesis: cutting field lists the schema requires changes no behavior — disconfirmation: a run-8 or run-9 record defect on one of those three fields that the validator did not catch]`.

### D46 — Agreement with itself is a property of every review check; observations on a pass are triaged (`layer_5`)
Source: RF-27, four times in run 8. Four review gates opened as designed (the mutant failed, the real artifact passed) while the reviewer listed real defects the check had not named: internal inconsistencies between a stated count or total and the content beside it. Each time the lead revised the check post hoc (cause (c)) to admit internal consistency, failed the artifact, and corrected — legitimate, but the same revision four times is a missing rule. In computer-science terms: a check is a predicate over the artifact, and consistency (no two parts of the artifact, or the artifact and a file it reads, assign different values to the same thing) is a predicate every artifact must satisfy regardless of the check's subject; it was being rediscovered per node. Now every review check carries it unlisted, the brief says so, and the mutant class "a contradicting count" is available on any node. The second half: an observation outside the check on a passing gate had no path in v3.1; it now has three (revise, open issue, nothing) and the choice is a recorded decision.
`[Hypothesis: with the standing property, no run-9 check revision adds internal consistency — disconfirmation: one that does]`.

### D47 — Gate code is sequestered from builders; a brief's interpretation is a ruling first (`layer_2`, `layer_5`)
Source: RF-26 and RF-30 (twice). A builder opened the gate scripts in `code/` and shaped its output to them, including a line written only to satisfy a structural check — the builder optimized for the gate, which is what separation of duties exists to prevent, one level below the builder/reviewer line. Separately, the lead twice wrote an interpretation into a reviewer brief (a reading of a given that contradicted an accepted artifact; a truncated given) and the reviewer failed real sentences on it; both reviews were void and cost a rerun each. A brief that interprets a given is a check revision in disguise: it changes what the reviewer tests without the was/now/reason the prompt requires for a revision. Now the gate's program is on the builder's `Sequestered:` line for non-code outputs (code nodes keep their gate test, which is the specification), and any interpretation the lead adds to a brief is a ruling recorded before dispatch; a fail resting on a ruling that an accepted gate read the other way is void and the ruling, not the artifact, is revised.
Falsifiability: threshold: a run-9 void traced to a brief interpretation that was not recorded, or a builder self-report naming the gate script; horizon: two runs; role: lead at the record.

### D48 — The reviewer receives the node's `reads` (`layer_5`)
Source: RF-29. A second review failed a rationale for resting on a line that did not support it; the line rested on a fact stated in another of the node's inputs, which the reviewer had not been given. The builder's citation was missing, so the fail stood, but the reviewer's confidence came partly from an input it was not shown. The builder brief lists the node's `reads`; the reviewer brief did not. In CS terms: the reviewer evaluates a predicate whose free variables include the artifact's inputs; withholding an input makes the predicate undecidable and the reviewer guesses. Now the review brief carries the same `reads` paths.
`[Hypothesis: no run-9 review fail cites "no line says this" for a fact that a file in the node's reads states — disconfirmation: one that does]`.

### D49 — A correction reserve inside {{LIMIT}} (`inputs`, schema `usage.reserve_runs`, X30)
Source: RF-33. Run 8 reached 50 of 50 with a known one-token defect (missing `(gN)` citations) and no path to spend one builder return on it; the prompt's only options were partial delivery or the lead editing an artifact. A hard limit that forbids a one-line fix is a cost with no benefit: the limit exists to stop runaway correction loops, not to freeze a known fix. Now the last tenth of {{LIMIT}} (rounded up) is a reserve spendable only on a one-item correction return and its re-gate, recorded in `usage.reserve_runs` and bounded by X30 (at most ceil(limit/10) entries, each a correction attempt with a checks row); in interactive mode at the limit with such a fix outstanding the lead asks the person to raise the limit before delivering partial. The reserve is inside the limit, not added to it, so the ceiling the person set is unchanged.
Falsifiability: threshold: a run that delivers partial on a token-class defect with the reserve unspent; horizon: three runs; role: lead at delivery.

### D50 — Tooling gets a cold read before baseline; filter-evading rewrites go to the residue reviewer (`principles`, `layer_2`)
Source: RF-28 (twice), RF-31, RF-25 (twice). Programs copied from an earlier run kept that run's paths and lists and checked the wrong things. And two builders reworded sentences to pass a filter and said so in their self-reports — the only reason the lead knew. Three facts about `partial` filters and copied tooling: a program carried between runs carries the previous run's constants; a pattern list is a specification that was never cold-read; a filter's silence after a builder has seen it flag proves little. Now: every `exec` command names its root or runs from {{OUTPUT}}; a carried program is read for run-specific constants; a `partial` filter's patterns are asked once what they would miss; and every sentence a builder changed to satisfy a filter is named in its self-report and handed to the residue reviewer. Each is a decision in the record.
`[Hypothesis: no run-9 finding traces to a path, file list, or pattern carried from a previous run — disconfirmation: one that does]`.

**T-24 on v3.2 (first cold read, opus).** All five passages were rewritten after the read. Findings the reader supplied beyond the passages' own ambiguity: (F-20) a pre-existing defect — audits count against {{LIMIT}} and must run before every delivery, so a run that reached its limit exactly could never fund its own audits; the reserve sentence now exempts the two audits from the stop; (F-21) the first draft sent the builder's filter-evading sentences to the residue reviewer "in the self-report", which the reviewer's `Sequestered:` line withholds — a direct contradiction one sentence apart; now a separate `filter_edits:` field the lead hands over; (F-22) "the builder never reads the gate" collided with "may run the check against the saved file" — now run-but-not-open, with "open a sequestered gate program" on the may-not list and the rule-encoded node's output gate covered; (F-23) "patterns are asked what they would miss" named no one — the lead judging its own filter breaks separation of duties, so a fresh subagent asks, counted. The reader's rewrite of the reserve sentence was adopted nearly verbatim. Two schema-redundant sentences cut under D45 (degraded review verdict; `exec_available: no` design-time record): −45 words.

**T-24 second read (opus).** Four of five passages read one way; two gaps fixed: the review brief's "exactly" list had no slot for the decision on what a filter would miss (the output of D50's question had nowhere to go), and "an accepted artifact" in the ruling-void rule did not say whether it includes the artifact under review when it was accepted earlier — now "any artifact accepted before that verdict", counting toward escalation. Two consequences the reader derived that the draft had not intended, fixed: the reserve had admitted only the integration *rerun* a correction triggers, so a run whose last node was accepted inside the reserve could never run integration for the first time; and re-gates a failed evidence audit requires were barred. Both now admitted. The reader also named a hole, not an ambiguity: `filter_edits:` sits outside the one-item rule and nothing checks it is honest — a builder could label a substantive change a filter edit. Left as is; the residue reviewer reads the list against the artifact, which is the check. Final: 3,365 words.

### D51 — A quotable contradiction is a verdict, never a borderline (`layer_5`)
Source: RF-35 (run 9, twice). D46 put agreement-with-itself in every review check; two reviewers then found a contradiction, called it "borderline", and passed, and the lead had to revise the check to name the property before it could re-gate (T-29's two misses). The property existed; the reviewer's threshold for applying it did not. Now the brief states it as a verdict rule — a count, list, label or cross-reference contradiction the reviewer can quote is a fail — and the return has no third value. The first cold read found the draft's "a contradiction" wider than the property (any contradiction would void the review under the not-in-`fails_when` rule); scoped to "of that kind". When the quoted `reads` value is the wrong one, cause (b) applies, not the parenthetical's default (a).
`[Hypothesis: no run-10 check revision adds an internal-consistency property — disconfirmation: one that does, as in T-29]`.

### D52 — `filter_edits:` defined, and `none` is a claim (`layer_2`)
Source: RF-34 (run 9). One builder disclosed filter-driven rewordings under the field; another returned `none` while its self-report described rewording flagged sentences — it did not classify its own edits as filter edits. The field now has a definition ("every sentence changed after a check listed it, for whatever reason", cumulative, the builder's own check runs included), `none` is a claim the self-report must not contradict (the lead rebuilds the list from the two versions under a decision), and the cold read's hole is closed: on a retry, every listed edit belongs to the one `changed:` item, or the attempt is failed.
Falsifiability: threshold: a run-10 builder whose self-report describes a rewording its `filter_edits:` omits; horizon: two runs; role: lead at the return.

### D53 — A copied value is a `reads` edge (`sizing`)
Source: RF-36 (runs 8 and 9 — a promoted lesson). One output copied counts from another node's output; in both runs the source changed after the copy was gated and the copy went stale, caught by a human each time. A copy is a data dependency the graph did not draw. Now a spec that copies a value from another node's output names that node in `reads` (so the DAG orders them), mutual copies merge or read a third node (the cold read's cycle case), and a copy found after approval gets its edge and a re-gate under a decision — the return path the first draft lacked.
`[Hypothesis: no run-10 stale copy is found by a reader — disconfirmation: one found by any reviewer or auditor]`.

**T-24 on v3.3 (one cold read, opus).** All three passages read two ways on first read; each rewrite above adopts the reader's chosen reading: the copy rule names the cycle and the post-approval path; the verdict rule is scoped to the standing property's kind and attributes a wrong upstream value to cause (b); the `filter_edits:` rule gets a consequence for a false `none` and keeps the one-item rule on retries. The reader's proposed rewrite of the last was adopted in substance.

**T-26 retired.** The pre-registered measure (correction share of budget under 25%) failed in run 8 at 40% against run 7's 44% and was the wrong measure: D41/D42 cut the cost of each correction (every run-8 correction was one return, two runs; run 7's integration fix was eight) without cutting the count, which rose with the number of review gates. Replacement measures, both already in the record: cost per correction (runs per fix; run 8: 2.0) and first-attempt review pass rate at the node level (run 7: 6/9; run 8: 5/14, depressed by four mid-run check revisions that D46 removes). Pre-registered for run 9: cost per correction ≤ 2.0 and first-attempt pass rate ≥ 60%.

---

### D54 — Integration and audit runs are reserve events of their own kind; the audits alone may pass {{LIMIT}} (`inputs`, `exit`, schema `usage.reserve_runs`, X30)
Source: external review of the v3.3 kit (Codex handoff, DESIGN-01), confirmed against run 9. D49's prose admitted the integration node and the two audits into the reserve and said the audits run "whatever the count", but the schema's reserve list could only hold correction returns and re-gates (attempt ≥ 2 with a node row), so run 9's two reserve runs (the integration review at 23, the evidence audit at 24 — RF-38) were unrepresentable, and "whatever the count" contradicted the exit line's hard {{LIMIT}}. The reviewer's adapter resolved the contradiction the other way (hard cap; an unrun audit makes the run partial). This version resolves it in the prompt's favour and makes the record able to say so: the reserve list has four kinds — `correction_return`, `re_gate` (node + attempt ≥ 2), `integration` (attempt, no node; its gate is the acceptance items), `audit` (name, no attempt) — only non-audit entries count toward ceil({{LIMIT}}/10), and `consumed` may exceed `limit` by at most the number of audit entries. The reasoning: an unrun evidence audit ships uncited claims as if graded; two runs past the limit are cheaper than that, and a limit the audits may pass by exactly two is still a limit. The adapter's choice stays available to a host with a hard cap — it then records the unrun audit and delivers partial, which the schema already expresses.
`[Hypothesis: every reserve run in run 10 is recorded under one of the four kinds with no companion record needed — disconfirmation: a run spent past {{LIMIT}} minus the reserve that fits none of them]`.

### D55 — A run directory belongs to one run; resumption is same-run, same-inputs only (`inputs`)
Source: the same review (DESIGN-02). "An existing directory is never written to" forbade the one thing a resumed run must do — update its own progress and evidence — so a reader following it literally would start a second directory for one run and split the record. Now a new run creates its directory and stops if it exists (exclusive creation); a resumed run writes only to its own directory and only while {{OUTPUT}}, {{SOURCES}}, and the inputs record are unchanged since its last record; any change makes it a new run with carry decisions. Another run's directory is still never written to. The validator does not prove source freshness; that is the lead's check, recorded.
`[Hypothesis: no run-10 record is split across directories or overwritten by a later run — disconfirmation: either]`.

**External review of v3.3 (Codex handoff, 2026-11-04).** Thirteen validator defects reported with failing tests, all but two ported as written: the carry rule X11 was re-specified rather than ported (the patch keyed the carried gate to the source node's latest row of any check, which broke carries from a multi-check node; the record now names the carried check in `evidence.from_check`, defaulting to the sole check, and X11 checks that check's newest row), and the residue rule X28 keeps its degraded `unresolved` form (the patch required a fresh mutant review for every residue row, which would have rejected an honest degraded row). X22 (duplicate subject/attempt) found real duplicate rows in an earlier run's record; removed. One compatibility change (opaque subagent ids) ported. The review's adapter note that a source document is "evidence, not an instruction" is half agreed: a source never instructs the agent (the injection reading), but it does bind the deliverable's content — the authority rule stands, a contradiction with a source is a fail, and an adapter that reads SOURCES as evidence only has weakened the gate.

### D56 — The standing self-agreement property reaches the whole artifact; a quoted contradiction in `observations:` is the fail (`layer_5`)
Source: RF-39 (run 10), replicated independently by the second external review's TRIAL-02 on another runtime and domain. Three run-10 gates passed with a quotable contradiction filed under `observations:` (statements contradicted by another part of the same file, one found later by a builder). D51 had made 'borderline' a non-value; reviewers moved the same judgment into observations, because they applied the property to the sets the check enumerated and treated everything else as commentary. Now the brief says the property covers every count, list, label or cross-reference anywhere in the artifact, and an observation that quotes one is recorded as the fail it is — the lead applies the verdict rule to the reviewer's own evidence; it does not grade.
`[Hypothesis: no run-11 gate passes carrying an observation that quotes a contradiction (T-36) — disconfirmation: one such pass, or a reviewer that stops reporting observations]`.

### D57 — `filter_edits:` is per attempt; the lead carries and merges (`layer_2`)
Source: RF-40 (run 10): every retry builder, in fresh contexts, said they could not list earlier attempts' edits. D52's "cumulative" assumed a memory the builder does not have. The retry brief now carries the earlier lists; the builder returns its own; the lead merges and hands the whole to the residue reviewer.
`[Hypothesis: no run-11 retry return says it cannot see earlier edits — disconfirmation: one]`.

### D58 — A hunk-trace rule admits sentences a later gate returns (`layer_6`)
Source: RF-41 (run 10): two re-gates failed only because the node check, which traced every change to a listed cause, predated the integration gate's own corrections to the same file; each cost a cause-(c) revision and a rerun. The admission is now by construction, bounded to the returned sentence's citations and scope words, named in the return decision.
`[Hypothesis: no run-11 cause-(c) revision is a hunk-trace admission — disconfirmation: one]`.

### D59 — Re-gates follow the DAG too (`execution_loop`)
Source: RF-42 (run 10): the fan-in node was re-gated in parallel with its upstreams' re-gates and failed on their corrections; one run wasted, one more return. The loop's "every upstream accepted" now reads "at its newest attempt", for first runs and re-gates alike.
`[Hypothesis: no run-11 node fails a re-gate on an upstream change that postdates its dispatch — disconfirmation: one]`.

### D60 — A residue review over a set reads every file and returns a ledger (`layer_7`)
Source: RF-43 (run 10): given two file sets differing by one planted sentence, the residue reviewer diffed and grepped (void); told to read and ledger each file, the rerun found pre-existing over-claims the mutant design had invited it to skip. A diff or pattern-search verdict is void by rule; the mutant stays.
`[Hypothesis: run-11's residue reviews return per-file ledgers and no void — disconfirmation: a void for method]`.

### D61 — Unchecked rules are in the record before approval (`layer_7`, schema `progress.unchecked_rules`, X32)
Source: the second external review's V34-01 (their readiness companion). Deliverable rules could be exercised only implicitly. The prompt promised the mapping; the schema could not see it. Now every deliverable rule is named in a check row's `exercises` or listed as unchecked with a reason, and X32 holds at approval. Sealing and fingerprinting (the rest of their companion) stay in the Codex adapter.
`[Hypothesis: run-11's delivery lists no rule as unchecked that a check in fact exercised — disconfirmation: one found by the audit]`.

### D62 — A removal check names its element set (`layer_5`, RF-52, RF-54)
Source: run 12's tests node. The check read "fails if the clause's behaviour is removed"; three reviewers read it at three grains (clause, element, ~215 program edits) and each later one found gaps the earlier did not, so the builder was chasing a set it could not see and the node failed on its third attempt. Now the check names the set — an enumerated list per clause or the lead's mutant list — bounded to what output, exit code or files make observable (C39's "opens for reading only" was unobservable and was demanded anyway). An element a reviewer adds outside the set is an observation, triaged into a check revision.
`[Hypothesis: with a named set, a suite node closes in ≤ 2 attempts — disconfirmation: a third attempt on a node whose check names its set]`.

### D63 — Parametrized cases are one test (`layer_5`, RF-53)
Source: run 12. Reviewer 2 required a second C29 case; reviewer 3 failed the two cases as "one shared reason" — the check both required and forbade the sample set. Distinctness is now between tests naming different elements; a parametrized test's cases are one test.

### D64 — The evidence audit samples the newest row per subject (`layer_7`, RF-55)
Source: run 12's audit, which graded two superseded `tests-exec` rows miscited (they cited "84 passed" and "115 passed" for a file later attempts overwrote) and failed at 40%. A superseded row's citation was true when written and has no artifact to rerun against; sampling it measures the lead's housekeeping, not the evidence. Alternative kept open: snapshot each attempt's artifact under the record, which keeps every row reproducible at a storage cost.

### D65 — The label draw lives under the record (`layer_5`, RF-56)
Source: run 12's post-hoc review, where the lead left `G-mutant.txt` beside the sets and the reviewer read it. The draw is written under {{RUN_DIR}} only.

### D66 — Exec evidence carries absolute paths (`layer_7`, RF-57, X33)
Source: run 12's auditor had to prefix `cd /home/claude/run12 &&` to four cited commands. A citation that depends on the lead's working directory is a citation the auditor must guess at; X33 flags an exec evidence command whose first `cd` is relative.

**Lead error recorded (run 12).** The spec reviewer observed "C12 lists four evidence kinds; the schema has five"; the lead triaged it as nothing because `not_run` cannot sit on a pass row. The post-hoc reviewer counted it as a defect. D56 already says a quotable contradiction with a cited source is a fail whoever notices it; the triage was wrong by the kit's own rule. No new rule — a note that D56 binds the lead's triage as much as the reviewer's verdict.

**Measured cost of the route (run 12).** First graph-vs-direct pair, pre-registered: 16× subagent tokens, a partial record, 1 post-hoc defect vs 4 (results in the repository's `CALIBRATION-LOG.md`, Run 12 entry). The applicability guidance stands; its cost side is now a number, with the caveats listed there.

**Reserve under a raised limit (RF-44, note on D54).** The reserve list holds one reserve; a raise re-bases it, and the raise decision names the runs spent under the old one. No schema change.

**External review, second round (2026-11-04).** Five findings, two validator gaps closed (X27 enforced; X12 exempts a literal source quote), one process gap (D61), two adapter-side; their trial replicated RF-39. Dispositions in the calibration log.

## 1a. Levers (operator-facing; not in the prompt)

| Lever | Where set | Effect |
|---|---|---|
| `{{MODE}}` | inputs | What pauses: approval, questions, irreversible steps |
| `{{LIMIT}}` + unit | inputs | When the loop exits; what counts against it (every subagent, reviewer, void review, code run) |
| `{{MODELS}}` | inputs | The tier ladder the tier rule walks |
| Tier-rule thresholds | layer_1 | How fast nodes climb the ladder; revisable one at a time via lessons.md promotion |
| `{{PRIORITIES}}` | inputs | Tiebreak for satisfiable-several-ways checks and conflicting `{{CHECKS}}` items |
| `{{SCOPE}}` + `Enforcement:` | inputs, layer_4 | Write boundary; whether it is tooling-enforced or instruction-only |
| `own gate` conditions | sizing | How many nodes get their own gate; tighten to reduce graph size |
| Correction cap (3) | layer_6 | Attempts before a node fails; not a lever in the prompt, change by editing |
| Promotion threshold (`confirmed in: 2`) | layer_6 | How fast observations become template defaults |
| Authority rule | inputs | Halt-form; fixed. Changing it to warn-form reproduces v1.1 behavior |
| Unchecked tolerance | layer_7 | The run may complete with unchecked rules; tighten by adding a maximum unchecked count to {{CHECKS}} |
| Evidence-audit threshold (10%) | layer_7 | How many miscited rows fail the audit outright versus revert individually |
| `dissent` eligibility | layer_6 | `review` gates only; widen to `inspect` only by editing, and expect more `partial` runs |

---

**L6 — Whether to open a record at all (third external review, selection.md).** The graph is for dependent outputs with separate acceptance, multi-source reconciliation, or a handoff; a lookup, a status check, an isolated edit with a known test, or a one-outcome batch is run directly. Size is not the threshold. The lead records the choice in one line when it declines a record for a task someone might have expected one for.

## 2. Per-layer rationale and self-checks

Each section names the Guide rule applied and confirms the prompt's text with its surface feature.

**inputs.** Stage 1 output shape (Problem / Goals / Constraints / Assumptions / Unknowns / Risks) replaces "restate in your own words" because an unshaped restatement has no checkable completeness. `changes outcome: yes | no` makes the one-question selection a filter over a visible list. `guarded by:` on every Risks entry (D19) forces each risk to a node or an explicit acceptance. `{{PRIORITIES}}` (D18) is a separate input per the Guide's Stage 3 design. Retained judgment qualifier: "largest consequence" — no observable surface exists without pricing every unknown, which costs more than the question.
*Self-check: subjects `Every Unknowns entry` and `Every Risks entry` are bare; permitted values closed, with `None — accepted` for the absence case; RULE-001.*

**sizing.** `split reason:` converts "do not manufacture nodes to look thorough" from self-monitoring into a required field with a closed value set. `own gate` conditions are the observable rewrite of v2.3's "risky enough" (RULE-004); the `risk` citation (D19) ties each to framing.md.
*Self-check: subject `Every node in graph.md` is bare; permitted values include `None — single-node graph`; RULE-001, RULE-004.*

**layer_1_split.** `does:` and `shape:` (D17) make the task enumerable and the output's sections declared; name-match before approval (D14) is the producer half of RULE-P01 that v2.4 lacked. `rules:` and `program considered:` convert "do not stretch rule-encoded" into a field that cannot be filled for a judgment task. The tier rule (D15) replaces the `because:` clause: tiers now follow counted spec properties, and the rejection clause polices values outside the list rather than cost-shaped reasoning. Brevity allowance is RULE-008 (eleven fields > four). The test-first obligation stays as a conditional rule ("For a node whose output is code") because the trigger is the `kind:` + output type, a visible spec property. *Surface-feature unavailable:* none needed — `kind: code` is the trigger.
*Self-check: subject `Every node spec in graph.md` is bare; each field's permitted values include a `None` / `n/a` entry where absence is legitimate; the tier rule is a closed list of counted conditions; RULE-001, RULE-004, RULE-008, RULE-P01.*

**layer_2_nodes.** Brief contents are enumerated and ordered ("contains exactly, in this order") so an incomplete brief is a missing line, not a judgment. The role line (D17) is the Guide's per-stage identity. `Sequestered:` is RULE-P02. `changed: <one item>` (D16) is the format rule for the "one change per node run" principle; two items is a visible failure. The failure hypothesis line is RULE-006 applied to diagnosis; the retry is the cheapest disconfirming observation, so no extra cost. "Self-report of at most five lines" replaces "short" (RULE-004).
*Self-check: subject `Every builder brief` is bare; `Sequestered:` permitted values include `None — nothing withheld`; `changed:` permitted value count is one; RULE-001, RULE-006, RULE-P02.*

**layer_3_code_nodes.** Format rules precede the kind definitions (RULE-003). Three borderline pairs at the three classification points (RULE-002). The two-gate rule for rule-encoded scripts fixes the RULE-011 audit finding from v2.3. `tried:` on blockers is RULE-018 absence enumeration.
*Self-check: subject `Every code node spec` is bare; `rules:` permitted values include `None — deterministic`; RULE-001, RULE-002, RULE-003, RULE-018.*

**layer_4_permissions.** Format rules first (RULE-003). The enforcement check is in Trigger / Steps / Output form (RULE-020) with a `[Verified: <config path>]` tag on the tooling claim (Part 3, Fabrication). "Near the boundary" is deleted; `{{SCOPE}}` membership is binary.
*Self-check: `Enforcement:` permitted values are a closed pair; the procedural command has all three blocks; RULE-020, Part 3.*

**layer_5_gates.** The reviewer brief is enumerated like the builder brief, with its own role line and a `Sequestered:` naming the builder's self-report, reasoning, and tests (D17, RULE-P02). Per-section verdicts follow the `shape:` declared upstream. "A return containing a fix or alternative is void" is the grep-able form of the D17 non-adoption. `exec/inspect unavailable: tried …; returned …` is RULE-018. `not run` vs red with a borderline pair is RULE-002. `removed:` restricted to a `fails when` property is the observable form of D8. "`proven` does not appear in any run file" is a grep-able prohibition (Part 3, Hallucination). Brevity allowance is RULE-008 (seven columns > four).
*Self-check: subject `Every edge` / `Every gate` / `Every variant record` bare; checks.md permitted values enumerated; RULE-001, RULE-002, RULE-008, RULE-018.*

**layer_6_return_paths.** Entry / Body / Exit labels are the loop-control convention. Cause recorded as `[Hypothesis: …]` is RULE-006. Cause (c)'s `was / now / reason` entry, with the "differs with no such entry voids the gate" clause, converts "never weaken a gate" from self-monitoring into a diffable condition. `confirmed in: <n>` makes promotion a count, and `scope:` is RULE-019 evidence scope.
*Self-check: subject `Every accepted result` and `Every entry` bare; cause list closed; RULE-001, RULE-006, RULE-019.*

**layer_7_completion.** Each "complete means" line is verifiable from run files alone (RULE-004). Partial status has a closed vocabulary.
*Self-check: every line confirmable from checks.md, graph.md, progress.md; RULE-004.*

**execution_loop.** Entry / Body / Exit labels. Step 2 fixes the v2.3 audit finding (gate test before code node). The cost-pressure line carries `Applies in all contexts` (RULE-012).
*Self-check: loop-control header present; RULE-012 applicability stated.*

**handoff.** `Override:` on "accepted nodes are not rerun" resolves the v2.3 contradiction with reusable specs (RULE-012). Sections are enumerated.
*Self-check: procedural constraint carries an `Override:` with mechanism and bookkeeping; RULE-012.*

**delivery.** Positive-form gap statement replaces any intention-shaped phrasing (Part 3, Anthropomorphism). The re-scan step is RULE-011 adopted as a standing obligation.
*Self-check: vocabulary closed; gap form named; RULE-011, Part 3.*

---

## 3. Applicability register (RULE-012)

| Constraint | Applicability |
|---|---|
| Lead runs on the most capable tier | Applies in all contexts |
| No agent grades an artifact it built | Applies in all contexts |
| Deterministic steps run as programs, never subagents | Applies in all contexts |
| Irreversible steps ask (interactive) or block (autonomous) | Applies in all contexts |
| Every gate opens on evidence, never confidence | Applies in all contexts |
| Reviewer tier ≥ builder tier | Applies in all contexts |
| Cost pressure never changes a check | Applies in all contexts |
| Accepted nodes are not rerun | Override: `{{SOURCES}}` differ from the recorded run; bookkeeping: new `{{RUN_DIR}}` + Decisions entry |
| A check changes only under layer_6 | Override: cause (c) by the lead; bookkeeping: `was / now / reason` in Decisions |
| A gate test changes only under layer_6 | Same as above |

---

## 4. Retained judgment qualifiers

RULE-004 asks for observable scope qualifiers. These four stay as judgment, deliberately, because an observable rewrite would be false precision:

| Qualifier | Where | Why it stays |
|---|---|---|
| "largest consequence" | inputs | Pricing every unknown costs more than asking the question |
| "two competent people" | layer_3 | The definition of deterministic; no cheaper surface exists |
| "a person would otherwise judge" | layer_3 | Same |
| "wrong in a way the brief covered" | layer_6 cause (d) | Distinguishing capacity from brief defect is the triage judgment itself |

---

## 5. Compliance-theater carve-out (Part 3)

The Guide's catch-all flags list entries under three words in substance slots. checks.md deliberately uses `none`, `not run`, `minimal — inspect`, `unresolved`. These are the honest-absence cases the Guide's own `None — <reason>` convention protects. The carve-out: the catch-all applies to `evidence` and `red evidence` only on rows whose verdict is `pass`. A short entry on a `fail` or `unresolved` row is the rule working.

Related symmetry: the Guide's diagnostic for compliance theater — *if I removed the rule, would the output change?* — is the discriminating-check principle (D4, D8) applied to rules instead of gates. The same test, one level up.

---

## 6. Changelog

**v3.5.1** — Run-12 findings (the first graph-vs-direct pair). Removal checks name their element set (D62). Parametrized cases are one test (D63). Evidence audit samples the newest row per subject (D64). Label draws under the record (D65). Absolute paths in exec evidence, X33 (D66). 3,793 → 3,933 words.

**v3.5** — Run-10 findings and the second external review. Standing self-agreement reaches the whole artifact; a quoted contradiction in observations is the fail (D56). filter_edits per attempt, lead carries and merges (D57). Hunk-trace rules admit returned sentences by construction (D58). Re-gates follow the DAG (D59). Residue reviews over sets read every file and ledger (D60). Unchecked rules in the record before approval, X32 (D61). Reserve re-based on a raised limit (RF-44). Validator: X27 enforced, X12 source-quote exception (second review). 3,601 → 3,822 words.

**v3.4** — External review (Codex handoff) and run-9 record. Reserve events of four kinds; the audits alone may pass {{LIMIT}}; schema `usage.reserve_runs` extended, X30 rewritten (D54). Run directory: exclusive creation, same-run same-inputs resumption (D55). Validator: thirteen reported defects fixed (X11 re-specified with `evidence.from_check`; X22 duplicate rows; X17, X23, X31 and CLI hardening; opaque subagent ids); 73 tests. No new behavioral rule for subagents. 3,501 → 3,601 words.

**v3.3** — Run-9 findings. A quotable contradiction is a fail, never a borderline; wrong upstream values are cause (b) (D51). `filter_edits:` defined; `none` is a claim; retry edits belong to the one item (D52). A copied value is a `reads` edge; mutual copies merge; a late-found copy gets an edge and a re-gate (D53). One cold read. 3,365 → 3,501 words.

**v3.2** — Run-8 findings. Agreement-with-itself as a standing property of every review check and triage of observations on a pass (D46); gate code sequestered from builders, brief interpretations recorded as rulings before dispatch (D47); the reviewer receives the node's `reads` (D48); a correction reserve inside {{LIMIT}}, schema `usage.reserve_runs` + X30 (D49); tooling cold read before baseline, `exec` commands name their root, filter-evading rewrites go to the residue reviewer (D50). Rulings R42–R46. T-26 retired; cost-per-correction and first-attempt pass rate pre-registered for run 9. 2,965 → 3,365 words (+400 after two cold reads and two D45 cuts: five additions, the largest delta since v2.9, and the first version where every addition traces to two or more occurrences; F-20 to F-23 from the read).

**v3.1** — Run-7 findings. Per-element verdicts on enumerable review sections (D41); token-fixable checks typed exec/partial (D42); input facts binding, derived into rules.yaml, bounded by "says no more than it says", conflicts with them blockers (D43); audit notes before counts (D44); three schema-redundant field lists cut (D45). Rulings R36–R41. 2,892 → 2,965 words. T-25 continues (second run pending).

**v3.0** — Run-6 findings and the first cut. Schema: `pending` disposition for an asked-but-unanswered unknown, X29 (D39). Prompt: cause (d) folded into (a); cost-pressure line, integration tiebreak, and threshold-promotion clause removed; check-vs-check conflict joins the authority rule; source defect renumbered to cause (d) (D40). 2,933 → 2,892 words. T-25 pre-registered. Rulings R29–R35.

**v2.9** — Run-5 findings. Schema v2: tier lines frozen at dispatch (D34); phase attribution for integration, delivery, and audit work (D35); `exec_available` per check with a residue path for heuristics over prose, `program_considered` removed, X28 added (D36). Prompt: exec availability decided per check; `partial` checks send their residue to a fresh reviewer with a planted miss; the reviewer brief's method adds no property beyond `fails_when` (D37). Fan-in tier line kept, pre-registered as T-22 (D38). 2,831 → 2,933 words after three T-24 cold reads (F-18: definitions belong in the schema, obligations in the prompt): D13's shrink hypothesis stays disconfirmed; the cut this round was a schema field, not prompt text.

**v2.8** — Format by reference (D-S). Record format moved to `graph-record/`; prompt keeps behavior only. 4,030 → 2,831 words.

**v2.7** — Calibration-driven. Authority rule in halt form (D27). rules.md derivation, `exercises:` on every check, `unchecked` in delivery, well-formedness against rules.md (D28). Cause (e) source defect (D29). `not run` isolation/red-evidence states, audits on every delivery, auditor `notes:` (D30). Green-at-baseline per gate, hash-carried integration verdicts, exact exit codes (D31). Nineteen ambiguity rulings per `graph-prompt-rulings.md` (D32). Vocabulary: mutant/mutation, separation of duties, Definition of Done, prerequisites/targets (D33). Builder stop rule in briefs. Integration writes integration.out, lead writes checks.md. Failed attempts as rows. progress.md section order mandated; `## Subagents` defined as the run record. Deliverable scripts live in {{OUTPUT}}.

**v2.6** — Transfers from PIPELINE-001 v1.0.0: evidence audit in a fresh context with a 10% threshold (D20); `Isolation:` field with degraded mode and a well-formedness consistency line (D21); verbatim anchors on reviewer fails, ≥1 not ≥3 (D22); integration node reruns from its first item after any correction (D23); record well-formedness as a code node (D24); verdict table with `dissent` and `escalated` terminals, `void`-twice → `escalated` (D25); `changed:` names the failed section, `cannot address:` alternative (D26). Non-transfers: no iteration cap (conflicts with `{{LIMIT}}`); Stages 2b/2b.1 as pipeline stages for arbitrary tasks (a node-template question). Prior-art convergence check on the prompt's own vocabulary run separately; the prior-art note behind it is not published.

**v2.5** — Design elements from the Guide's Part 1 pipeline, adopted individually rather than as a pipeline: producer-side `shape:` with name-match before approval (D14); tier rule on counted spec properties replacing `because:` (D15); `changed: <one item>` on retry (D16); role lines, `does:` mapped to `shape:`, per-section reviewer verdicts, enumerated reviewer brief (D17); `{{PRIORITIES}}` input carried to judgment briefs and the integration node (D18); Risks section in framing.md cited by `own gate` (D19); operator levers table (§1a). Deliberate non-adoptions recorded under D17.

**v2.4** — Two-file split per Guide authoring convention. RULE-001 conversions of eight self-monitoring lines (`split reason:`, `rules:`, `program considered:`, `because:` rejection clause, `removed:` restriction, was/now/reason on check revision, `{{SCOPE}}` membership binary, `tried:` on blockers). RULE-P01 named-field edges; RULE-P02 `Sequestered:` line. Stage 1 shape for framing.md. RULE-020 Trigger/Steps/Output on the enforcement check with `[Verified]`. RULE-008 brevity allowances on node spec and checks.md. RULE-006 hypothesis form on triage and diagnosis. RULE-018 absence enumeration. RULE-012 applicability register; `Override:` on rerun rule. RULE-011 audit fixes: two gates on rule-encoded scripts, brief contents include `needs`, gate test before code node in the loop. Entry/Body/Exit on the loop and correction edge. RULE-002 borderline pairs at four classification points.

**v2.3** — `{{MODELS}}`; `model:` per node with reviewer floor and fixed lead; programs-first with deterministic / rule-encoded split; cause (d) tier escalation; tier recorded in lessons.

**v2.2** — Test-first for code nodes: lead-fixed gate test file, assertion-level red, builder tests as evidence.

**v2.1** — Discriminating checks: `fails when`, `exec` red at baseline, deficient variant for `review` and integration, `red evidence` column.

**v2** — From the original: no self-grading, integration gate, run mode, typed checks, triaged correction loop, lessons separate from graph, run directory, sizing rule.
