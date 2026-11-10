# v2.7 rulings register

One ruling per open item. Each names its source (A-nn = auditor ambiguity, F-nn = calibration finding, O-x = observation, PA = prior-art row), the ruling, and the prompt location.

## Authority and derivation

| src | ruling | where |
|---|---|---|
| F-09, F-12 | `{{CHECKS}}` are necessary, not sufficient. Every specification named in `{{SOURCES}}` is binding. A conflict is a blocker (halt), not a design constraint. | inputs |
| F-13, F-15 | Before execution the lead derives a rule list from every spec in `{{SOURCES}}` (`rules.md`); each `{{CHECKS}}` item names the rules it exercises; rules with no item are listed as `unchecked` in delivery. The well-formedness audit runs against `rules.md`, not a fixed five lines. | layer_7 |
| F-05 | Triage cause (e): source defect — the unit is correct against the spec and wrong against `{{SOURCES}}`; blocker to the person: extend `{{SCOPE}}` to the source, or accept partial. Autonomous: partial. | layer_6 |

## Ambiguities (auditor numbering)

| # | ruling | where |
|---|---|---|
| A-1 (G-23) | Any field whose permitted values include `None — <reason>` or `n/a — <reason>` takes it only when the reason holds. The brevity allowance is deleted as a separate rule; it was a restatement. | layer_1 |
| A-2 (X-02) | "Run record" = progress.md `## Subagents`: one line per subagent, `<id>: <role> for <node>, <tier>`. Required section. | handoff |
| A-3 (C-08/09) | Red-evidence permitted values: baseline assertion failure with test path; `variant path: <p>; mutation: <property>`; `minimal — inspect`; `not run — <reason>` (only with verdict `unresolved`). `none` is removed. | layer_5 |
| A-4 (C-16) | Dissent evidence format: `reviewer: <excerpt>; builder: cannot address <section>; reason <text>`. | layer_5 |
| A-5 (P-01) | progress.md has a `## Enforcement` section whose single line is the permitted value. | layer_4, handoff |
| A-6 (P-04) | Isolation permitted values gain `n/a — code` for script audits. Every audit line in progress.md carries `isolation:`. | layer_5, layer_7 |
| A-7 (G-31) | Audits are not graph nodes. They appear in progress.md `## Audits` only. | layer_7 |
| A-8 (C-22) | Integration row red evidence = `{{CHECKS}}` baseline. Each review-type item inside integration has its own mutant record in its own row. | layer_7 |
| A-9 (G-09) | The `own gate` condition text quotes one of the four permitted conditions verbatim. | sizing |
| A-10 (G-08) | `inputs differ — <id>[, <id>…]`: several ids permitted, comma-separated. | sizing |
| A-11 (P-14) | Next action permitted values: a node id; `None — delivery`; `None — blocked on <open issue id>`. | handoff |
| A-12 (G-16) | A review check's content is the property under review, one line. | layer_1 |
| A-13 (C-11) | Literal `variant path:` and literal `mutation:`. | layer_5 |
| A-14 (exec evidence) | Exec evidence format: `<command>; expected exit <n>; actual exit <n>; <output excerpt>`. Exact exit code, never "non-zero". Closes F-08. | layer_5 |
| A-15 (C-19) | One checks.md row per `{{CHECKS}}` item, plus one `integration` summary row. | layer_7 |
| A-16 (X-10) | Failed attempts are additional checks.md rows, node column `<id> (attempt <n>)`. | layer_6 |
| A-17 (X-12) | Outputs lists `{{OUTPUT}}` paths only; run files are not Outputs. | handoff |
| A-18 (G-20) | `tier rule: none — lowest` when no line fires. | layer_1 |
| A-19 (order) | progress.md section order is the order listed in handoff. | handoff |
| G-32 | The integration node writes `{{RUN_DIR}}/integration.out`; only the lead writes checks.md. | layer_7 |

## Run findings

| src | ruling | where |
|---|---|---|
| F-01 | Green-at-baseline applies per gate (test file or command). A gate is valid when at least one case is red at baseline; green cases within it are kept. | principles |
| F-02 / D-04 | A review-gated artifact whose sha256 at integration equals its sha256 at its node gate carries that gate's verdict; otherwise a fresh review runs. | layer_7 |
| F-03 | Scripts that are the deliverable live in `{{OUTPUT}}`; run machinery lives in `{{RUN_DIR}}/code/`. | layer_3 |
| F-04 | `{{LIMIT}}` counts subagent, reviewer, audit, and code runs. Lead work before dispatch is reported in Usage as `lead: <tokens or n/a>` and not counted. | inputs, handoff |
| F-06 | Both audits run on every delivery, partial included. | layer_7 |
| F-07 | Isolation and red evidence take `not run — <reason>` on rows whose gate has not run; well-formedness accepts them only with verdict `unresolved`. | layer_5 |
| F-08 | See A-14. | layer_5, layer_7 |
| O-E | Auditor output has two parts: the row table, and `notes:` for anything outside the rows. Notes are recorded in progress.md Audits and never change a verdict. | layer_7 |
| O-B | Builder brief gains `If the check cannot pass on a correct artifact, say so and stop; do not edit inputs or the check.` | layer_2 |

## Vocabulary (prior-art rows 1, 2, 10, 11)

| old | new |
|---|---|
| deficient variant | mutant |
| `removed:` | `mutation:` |
| "a reviewer that passes both" (prose) | "the mutant survived" |
| "No agent grades an artifact it built" | named as separation of duties |
| "Complete means" list | named as the Definition of Done |
| `reads:` / `writes:` | parenthetical: prerequisites / targets |

Not adopted: `accepted` → `succeeded` (state vocabulary churn across every list; weak gain).


## v2.9 rulings (T-24, three cold reads of the three new passages)

The third reader's derived rule list matched the author's intent line for line (P1 15 rules, P2 8, P3 5). Ambiguity counts did not converge across the three reads (24 → 24 → 23); what converged was the rule list. Rulings for the readings that would change a lead's action:

| # | phrase | ruling | where |
|---|---|---|---|
| R20 | "a program can return the `fails_when` verdict" | in this environment, with a program the lead can write in the run; a tool that is missing is a `blocker` under layer_3, not `no` | layer_1_split |
| R21 | a judgment node carrying an `exec` check | the node stays a judgment node and runs as a subagent; the `exec` check gates its output. Gate type never changes node kind | layer_1_split |
| R22 | `partial` type | `exec` (schema enforces: `yes` and `partial` are `exec`) | schema `check` |
| R23 | residue verdict granularity | one `<id>-residue` row per attempt; the reviewer returns one verdict per flagged item inside it and the row fails if any item is a real miss | schema X28 |
| R24 | "false location" in the residue mutant | a file:line that is not where the sentence occurs (it may not occur at all); the reviewer who checks the location catches it either way | schema `residue` |
| R25 | the restated steps in the reviewer brief | they are the check item itself (the brief still has exactly five items); graph.yaml holds `content`/`fails_when` unchanged, the brief holds the steps, the revision is a `check_revision` decision naming the node | layer_5_gates |
| R26 | scope of a void on an added property | the whole review is void (one count shared with surviving-mutant voids toward `escalated`); it applies to a fail on the real artifact; a mutant failed only on an added property has not been discriminated and the review is void on that ground too | layer_5_gates |
| R27 | "each program considered" for `no` | at least one, at design time, in `node.unavailable.tried`, per node (one list covering its `no` checks); an analysis of what the program would return is enough | layer_5_gates, schema `node.unavailable` |
| R28 | residue review at baseline | not run; the baseline exec red is the assertion-level red for the program; residue reviews run at node gates | principles, X28 |

## v3.0 rulings (two cold reads of the rewritten cause (a), the authority rule, and the blocker sentence)

The second reader's rule lists matched intent (P1 7 rules, P2 6, P3 5). Readings that would change a lead's action:

| # | phrase | ruling | where |
|---|---|---|---|
| R29 | "a second (a) on the same node" | the second hypothesis of cause (a) on that node in the run, whatever came between; counts never reset within a run; "the same tier" is the tier of the attempt that just failed; a raised tier sticks for the rest of the run | layer_6 |
| R30 | "the reviewer raised to match" | reviewer tier := max(reviewer tier, new builder tier); a reviewer already above is left alone | layer_6 |
| R31 | "the move counted in the node's model" | `escalations` in graph.yaml's `model` increments by one; the as-run tier is what the model records (D34 freezes the `tier_rule` lines, not `escalations`) | layer_6, schema `model` |
| R32 | `{{PRIORITIES}}` versus a conflict | `{{PRIORITIES}}` orders ways of satisfying one check; it never chooses between two checks no artifact can satisfy together. That is a conflict, and a blocker | inputs |
| R33 | "the nodes it affects" for a check-versus-check blocker | the integration node and every node whose acceptance `exercises` names either check; in interactive mode the run pauses at the ask (run 6 did); in autonomous mode execution_loop's "critical-path blocker" exit is this rule applied when the blocked set contains the critical path | layer_3, execution_loop |
| R34 | "Every blocker, this one and the authority rule's" | every open issue of kind `blocker` or `source_defect`, present and future kinds alike | layer_3 |
| R35 | a layer_2 no-output return | counts as an attempt and, when its hypothesis cause is builder-side, as an (a) for R29 | layer_2, layer_6 |


## v3.1 rulings (one cold read of the four changed passages; rule lists matched intent on the first read; two passages reworded for the readings below)

| # | phrase | ruling | where |
|---|---|---|---|
| R36 | "token rather than thought" (P2) | judged per `fails_when` property at design time; a check with both kinds is split; choosing *which* token still counts as a token when the candidate set is closed (a name from a list), a thought when it is open. `inspect` remains available for a property the lead confirms by opening the file | layer_1_split |
| R37 | P2 and `{{CHECKS}}` items | the rule types the lead's node checks; a person's `{{CHECKS}}` item keeps its stated type, and the lead may add an exec filter beside it, never replace it | layer_1_split, layer_7 |
| R38 | "the brief names the set by rule" (P3) | the set is defined from the specification or the check (every cell, every row, every participant), never enumerated from one candidate, so an unlabeled A/B pair stays unlabeled; a missing element is then detectable | layer_5_gates |
| R39 | per-element coverage and excerpts (P3) | one verdict per element in the reviewer's return; a failing section carries one excerpt per failing element; the rule applies to the real artifact and the mutant alike, at node gates and at integration | layer_5_gates |
| R40 | "says no more than it says" (P1) | the test: split the claim into assertions; each must be entailed by the input's or specification's quoted text alone — no widened quantifier, strengthened modality, added number/name/condition/cause, or merged conclusion. Citation presence is token-fixable (exec/partial); overreach is a thought (review), with a mutant that adds one unsupported qualifier | inputs, layer_5 |
| R41 | "notes first, then counts" (P4) | per audit: the evidence audit's notes verbatim, then its tallies and pass/fail; the record audit's first failing rule (if any) then exit code; a degraded audit is reported as degraded with whatever it returned | delivery |

R42 (run 8, residue review). *Does a diagram label or node name need a (gN) citation when it names the content of a given?* No. The givens check applies to sentences that assert a given. A label is a name, not an assertion; the prose that introduces or describes the diagram carries the citation, and the reviewer reads label and prose together. A diagram with no describing prose is a different defect (an undocumented picture), caught by the readability priority, not by the givens check.

R43 (run 8): withdrawn — it ruled on a client-specific given. The lead had written a contrary reading of that given into the reviewer brief; the review it produced is void.

R44 (run 8, integration check). *May an output cite an input fact id from a previous run?* Yes, when a given of this run says those inputs stand. The input id is then a given by reference, and the output counts as citing a given; the reviewer brief lists the input's text beside the givens.

R45 (v3.2 cold read). *May the reviewer's `observations:` be read as "a proposed fix or alternative", which voids a review?* No. An observation names a defect or a tension and stops there; a proposed fix names a change to make. The return's `observations:` field is for the former; a reviewer that writes the latter anywhere in its return is void as before.

R46 (v3.2 cold read). *Does a contradiction between the artifact and a file in `reads` fail this node or reopen the upstream one?* This node, cause (a): the artifact copied a value and the copy is wrong against the file as it stands. Cause (b) applies only when the upstream file's value is itself wrong, which this property cannot see; that is found by the upstream node's own gate or by the evidence audit.

### R47 — A markdown link's label is a name (run 10)
A link's label — a heading or a path — is a name, not a sentence, for the givens filter and its residue reviewer; the sentence around the link is still checked. Extends R42.
