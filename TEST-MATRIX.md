# Test coverage matrix (kit v3.5.3, 2026-11-05)

Source of truth for what the calibration apparatus has exercised. An interactive version (not published) also exists, with an evidence grid, return-path transition coverage, and Pareto and set-cover views. Runs 1–6 predate the v3 record and are not counted. Keys (Gnn, Inn) name conditions; the set cover targets those whose status is `never` or `partial`, and a condition marked `covered` (G06, for one) is not open.

## 1. Conditions and evidence

| key | group | dimension | condition | runs | validator | pre-reg | status | note |
|---|---|---|---|---|---|---|---|---|
|  | Task | artifact kind | non-code deliverable | 7, 8, 9, 10 |  |  | covered |  |
|  | Task | artifact kind | code + contract + test suite | 11, 12 |  | T-36–T-41 | covered |  |
| G01 | Task | artifact kind | mixed prose and code in one graph |  |  |  | never | every run so far is one kind |
|  | Task | artifact kind | the kit itself as the task | 11, 12 |  |  | covered | both kit tools came from graph runs |
| G02 | Task | task size | 1 node |  |  |  | never | the prompt says one node is a valid graph; never run |
|  | Task | task size | 2–4 nodes | 11, 12 |  |  | covered |  |
|  | Task | task size | 5–8 nodes | 7, 9, 10 |  |  | covered | node counts from the log's Nodes: lines |
|  | Task | task size | 9+ nodes | 8 |  |  | covered | 9 nodes (run 8) |
|  | Task | dependency shape | chain | 7–12 |  |  | covered |  |
|  | Task | dependency shape | fan-out from one upstream | 7–10 |  |  | covered |  |
|  | Task | dependency shape | fan-in, 3+ upstream into one node | 10 |  |  | covered | a node reading three or more upstream outputs; D59 came from it |
| G03 | Task | dependency shape | diamond (fan-out then fan-in) with a re-gate |  |  |  | never | would exercise D59 twice on one path |
|  | Task | sources | one source set | 11, 12 |  |  | covered |  |
|  | Task | sources | several sources reconciled | 8, 10 |  |  | covered |  |
| G04 | Task | sources | a defective source (cause d) |  | schema: source_defect |  | never | the schema has the shape; no run has hit it |
|  | Graph | node kind | judgment node | 7–12 |  |  | covered |  |
|  | Graph | node kind | code node (no model field) | 11, 12 | test_v2_rules |  | covered | run 11 found the schema conflict for a judgment node whose output is code |
|  | Graph | node kind | node with a partial filter check (filter_edits, D57) | 10 |  | T-40 | covered |  |
|  | Graph | gate type | exec gate | 10, 11, 12 |  |  | covered |  |
|  | Graph | gate type | review gate | 7–12 |  |  | covered |  |
| G05 | Graph | gate type | inspect gate |  | schema: na_inspect |  | never | no row of type inspect in any shipped record |
|  | Graph | gate type | mutant-backed review | 8–12 |  |  | covered |  |
|  | Graph | gate type | residue review over a file set (D60) | 10 |  | T-40 | covered |  |
|  | Graph | mutant kind | planted contradiction with a given or source | 12 |  |  | covered | spec, docs, post-hoc |
|  | Graph | mutant kind | removed element (coverage gap) | 12 |  |  | covered | survived once, caught on the rerun |
|  | Graph | mutant kind | cannot-fail test | 12 |  |  | covered | tests attempts 1, 2 |
|  | Graph | mutant kind | baseline stub as the red state | 11, 12 |  |  | covered | gate tests red on the stub before dispatch |
|  | Graph | tier | haiku builder | 11, 12 |  |  | covered |  |
|  | Graph | tier | sonnet builder and reviewer | 7–12 |  |  | covered |  |
| G06 | Graph | tier | opus at any role | 10 |  |  | covered | escalation of one node to opus (RF-46) |
|  | Graph | tier | escalation 1 (one tier up) | 7, 8, 10, 12 |  |  | covered | RF-22, RF-46; run 12 tests node, haiku → sonnet |
| G07 | Graph | tier | escalation 2 (capped at the top) |  |  |  | never |  |
|  | Return paths | correction cause | (a) builder error | 7–12 |  |  | covered |  |
| G08 | Return paths | correction cause | (b) upstream field wrong — upstream reopens |  |  |  | never | the one return path that reopens an accepted node |
|  | Return paths | correction cause | (c) check wrong — revision with was / now / reason | 10, 12 | check text match |  | covered |  |
| G04 | Return paths | correction cause | (d) source defect — blocks until a person decides |  | schema |  | never | same condition as the defective-source row |
|  | Return paths | attempt depth | accepted at attempt 1 | 7–12 |  | T-28 | covered |  |
|  | Return paths | attempt depth | accepted at attempt 2 | 10, 11 |  | T-27 | covered |  |
|  | Return paths | attempt depth | accepted at attempt 3 | 10 |  |  | covered | an exec gate at attempt 3 |
|  | Return paths | attempt depth | fails at attempt 3 → node failed, dependents blocked | 12 |  |  | covered |  |
| G10 | Return paths | attempt depth | dissent (same section fails twice, cannot address) |  | schema: dissent |  | never |  |
| G11 | Return paths | attempt depth | escalated node on the critical path |  | schema |  | never |  |
|  | Return paths | review outcome | void: mutant survived | 12 |  |  | covered |  |
|  | Return paths | review outcome | void: verdict covered fewer than the set | 10 |  |  | covered |  |
| G12 | Return paths | review outcome | second void on one gate → escalated |  |  |  | never |  |
| G13 | Return paths | review outcome | fail resting on a property outside fails_when → void |  |  |  | never |  |
|  | Return paths | check revision | one revision on a node | 10 |  | T-32 | covered |  |
|  | Return paths | check revision | two revisions on one node | 12 |  |  | covered | tests node |
| G14 | Return paths | check revision | ruling-based fail voided by an accepted artifact |  |  |  | never |  |
| G15 | Return paths | builder return | cannot address: (triggers cause c triage) |  |  |  | never |  |
| G29 | Return paths | review check | a removal check that names its element set (D62) in a real run |  |  | T-42 | partial | rule exists since v3.5.1; no run yet |
|  | Record / validator | schema | schema rules via generated mutants |  | gen_fixtures 596 mutants, 591 expected caught, 591 caught (current tree) |  | covered | 0 gaps, 0 over-strict; the 5 mutants not expected caught are deletions of optional fields; the 594-mutant figures in CALIBRATION-LOG.md are from earlier versions |
|  | Record / validator | cross-file rules | X01–X33 positive path |  | 148 tests |  | covered |  |
| G16 | Record / validator | cross-file rules | a negative fixture for every X-rule |  | test_v2_rules (29) |  | partial | X03–X10 lean on the example record only |
| G17 | Record / validator | cross-file rules | X-rule hit on a real record | 10, 11, 12 |  |  | partial | hits found while writing records, never by a planned negative |
|  | Record / validator | reserve (D54) | no reserve runs | 11, 12 |  |  | covered |  |
|  | Record / validator | reserve (D54) | correction_return from the reserve | 10 | X30 | T-35 | covered |  |
|  | Record / validator | reserve (D54) | re_gate from the reserve | 10 | X30 | T-35 | covered |  |
| G18 | Record / validator | reserve (D54) | integration run from the reserve |  | X30 |  | partial | validator test only |
| G19 | Record / validator | reserve (D54) | audit taking consumed past LIMIT |  | X30 |  | partial | validator test only; run 10 stopped at the limit |
|  | Record / validator | reserve (D54) | LIMIT raised mid-run, reserve re-based (RF-44) | 10 |  |  | covered | unplanned |
|  | Record / validator | rule coverage (X32) | all deliverable rules exercised | 11 | coverage.py tests | T-41 | covered |  |
| G20 | Record / validator | rule coverage (X32) | unchecked rules listed with reasons |  | test_v2_rules |  | partial | no real record has used the list |
| G21 | Record / validator | rule coverage (X32) | uncovered rule → X32 fail at approval |  | test_v2_rules |  | partial | validator only |
|  | Record / validator | audits | both audits pass | 7–11 |  |  | covered |  |
| G22 | Record / validator | audits | evidence audit ≤10% miscited, rows revert | 8 |  |  | partial | 2.7% unfound in run 8; no pass row reverted |
|  | Record / validator | audits | evidence audit >10% → fail, inspect rows revert | 12 | X26 |  | covered | no inspect rows existed to revert |
| G23 | Record / validator | audits | degraded audit (same context) → partial |  | schema |  | never |  |
| G30 | Record / validator | audits | audit sampling newest rows only (D64) |  |  | T-43 | partial | rule exists since v3.5.1; run 12 produced the failure it fixes |
|  | Route | method | graph route | 7–12 |  |  | covered |  |
|  | Route | method | direct, no review (first delivery) | 12 D |  | P2 | covered |  |
|  | Route | method | direct plus one independent review | 12 D |  | P3 | covered | post-hoc |
|  | Route | method | Codex adapter run | Codex | compat/codex tests |  | covered | external lead; their trial replicated RF-39 |
|  | Route | lead | this assistant as lead | 7–12 |  |  | covered |  |
| G31 | Route | lead | Codex as lead | Codex |  |  | partial | adapter trials ran on v3.4, not the current prompt |
| G24 | Route | lead | a human as lead |  |  |  | never |  |
| G28 | Route | comparison | graph vs direct, pre-registered pair | 12 |  | P1–P4 | partial | one pair; T-44 asks for a second on a different task |
|  | Incidents (occurred) | harness | Write tool refused to a subagent | 12 × |  |  | covered | unplanned; resumed via message, heredoc save |
|  | Incidents (occurred) | harness | container restart mid-run (subagents lost) | 12 × |  |  | covered | unplanned, twice; the record replayed from next_action |
|  | Incidents (occurred) | harness | LIMIT raised mid-run by the person | 10 × |  |  | covered | unplanned, twice |
|  | Incidents (occurred) | harness | capability unavailable, recorded in unavailable.tried | 11, 12 | schema |  | covered | review-only checks (no exec, no inspect) |
|  | Incidents (occurred) | lead error | wrong triage of an observation (D56) | 12 × |  | T-36 | covered | C12 four-vs-five kinds |
|  | Incidents (occurred) | lead error | hypothesis entry recorded late | 12 × | X13 |  | covered | X13 caught the missing one on the rerun row |
|  | Incidents (occurred) | lead error | relative path in exec evidence | 12 × | X33 |  | covered | X33 added after |
|  | Incidents (occurred) | lead error | mutant label file readable by the reviewer | 12 × |  |  | covered | D65 added after |
| G25 | Measures | recorded per run | subagent tokens per run and role | 12 |  |  | partial | run 11 partial; runs 7–10 recorded node runs only |
|  | Measures | recorded per run | node runs vs LIMIT | 7–12 | X30 |  | covered |  |
| G26 | Measures | recorded per run | wall or subagent time | 12 |  |  | partial | from harness durations; not in the record |
|  | Measures | recorded per run | post-hoc defect count by a fresh reviewer | 12 |  | P3 | covered |  |
|  | Measures | recorded per run | mutant kill score on the suite | 11, 12 |  |  | covered |  |
|  | Measures | recorded per run | first-attempt reviewer pass rate | 9–12 |  | T-28 | covered |  |
| G27 | Measures | recorded per run | reviewer repeatability (same brief, N runs) |  |  |  | never | a statistic the kit has never collected |

Totals: 92 conditions — 62 covered, 13 partial, 17 never. Open conditions and injections not yet run (deduplicated): 44.

## 2. Return-path transition coverage

The layer-6/7 rules as edges of a state machine; 26 edges, 8 never traversed in any shipped record:

- never: gate → upstream reopens (cause b); gate → blocked (cause d); void → escalated (second void); gate → dissent, dissent → integration; escalated → partial; blocked → partial; at LIMIT → exit at LIMIT.
- traversed: everything else, including both cause-(a) edges, cause (c), review void → rerun, third-attempt fail → dependents blocked → partial, both audit outcomes, LIMIT reached → raised.

Reading: every edge that accepts work has been walked; the half of the machine that refuses work never has.

## 3. Failure injection

| key | failure | how to inject | what the kit should do | testable | status |
|---|---|---|---|---|---|
| I01 | Builder returns nothing or an error | Stub brief: return the single word error; or stop the agent mid-run | Layer 6: one attempt used; hypothesis entry before the retry | yes, deterministic | never |
| I02 | Builder returns partial output | Brief: write only the first section and stop | Same path; the gate must fail on the saved version, not the self-report | yes | unplanned in 12 (restart) |
| I03 | Builder writes outside its scope | Brief instructing a write to a sequestered path | D55 exclusivity; the lead's pre-gate listing diff catches it | yes | never |
| I04 | Builder reports gates passed without running them | Brief that forbids running the gate but asks for the standard return | The lead reruns every exec gate itself (rows carry na_exec / lead reran) | yes — the common real failure | never |
| I05 | Reviewer returns a proposed fix | Brief asking for 'and suggest the fix' | R45 / layer 5: the return is void; rerun | yes | never |
| I06 | Reviewer passes the mutant | Plant a mutant the brief does not point at; or a weaker tier | Review void; brief tightened; second void → escalated | yes | unplanned in 12 (tests attempt 3) |
| I07 | Reviewer reads leaked state | Leave a label file in its readable tree | D65 forbids it; the test is whether the lead notices | yes | unplanned in 12 (post-hoc G) |
| I08 | Builder and reviewer share a context | Run both in one context (same_context_degraded) | Isolation kind recorded; the run is partial | yes, by construction | never |
| I09 | LIMIT exhausted mid-graph | Set LIMIT below the graph's minimum runs (e.g. 5 for 4 nodes) | Exit at LIMIT minus the reserve for ordinary work; audits may pass LIMIT (X30); partial delivery names every node's state | yes, deterministic — the unit is node runs | never |
| I10 | Reserve consumed by a non-audit run | Force a correction when consumed = LIMIT − ceil(LIMIT/10) | X30 rejects; the lead stops or raises with an RF-44 decision | yes | never |
| I11 | Lead loses context (compaction) | Hand the record directory alone to a fresh lead with 'resume' | D55 same-run resumption: everything needed is in the record | yes — the central claim | unplanned in 12 (this session compacted); not measured |
| I12 | Container restart / subagent killed | Stop a background builder; delete any partial output | The record is a write-ahead log: nothing dispatched is lost that was not recorded; resume from next_action | yes | unplanned in 12 ×2 |
| I13 | Tool unavailable (no Write, no fresh subagent, no exec) | Remove the tool from the brief's allowance; exec_available: no | unavailable.tried records the attempt; the gate downgrades or the run is partial | yes | partial (review-only checks in 11, 12) |
| G04 | A source is defective (cause d) | Plant a contradiction in a frozen source | Open issue source_defect; blocks until a person decides | yes | never |
| I15 | Subagent token or context exhaustion mid-write | Not cappable from here; approximate with an oversized demand or a timed stop | Treated as partial output | partially — the state reproduces, the cause does not | never |
| G27 | Model nondeterminism | Run the same review brief N times on the same pair | Measurement, not a rule: agreement rate per tier | yes, as a statistic | never |
| I17 | Silent lead error (triage, late entries) | Cannot be injected into oneself; a second lead re-triages from the record | The adapter trials are this; the audit catches some classes | only by independent replay | unplanned in 12 (C12 triage) |

## 4. Proposed tests

Value 1–5 (5 = tests a claim the design rests on); cost 1–5 (1 = one call, 3 = a small dedicated run, 5 = a full run or a person's time); score = 2·value − cost, for comparison only. Schedule = greedy value-weighted set cover: at each step the test with the highest (open conditions still closed) × value ÷ cost; — means every condition it closes was closed by an earlier pick.

| cover # | score # | id | test | exposes | value | cost | score | when | closes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 3 | FT-03 | LIMIT wall: set LIMIT below the graph's minimum and run to exit | the exit rule, reserve arithmetic and partial delivery under a hard budget | 4 | 1 | 7 | own run | I09, G19, I10 |
| 2 | 9 | FT-10 | Subagent killed mid-run on purpose, then replay from next_action | the write-ahead-log property, measured rather than survived | 3 | 1 | 5 | next run | I12, I01, I02 |
| 3 | 15 | FT-15 | Negative validator fixture for every X-rule X03–X33 | whether each cross-file rule can fail, not only pass | 3 | 2 | 4 | next run | G16, G17, G20, G21 |
| 4 | 1 | FT-01 | Builder claims gates pass without running them; the lead's own rerun must catch it | the gate-as-oracle claim: pass rows rest on the lead's run, never the self-report | 5 | 1 | 9 | next run | I04 |
| 5 | 12 | FT-12 | Second void on one gate → escalated | the escalation path for a reviewer that cannot be made sensitive | 3 | 2 | 4 | own run | G12, G11, I06 |
| 6 | 14 | FT-14 | No fresh subagent available → same_context_degraded isolation and a degraded audit | what a degraded run records and whether it stays partial | 3 | 2 | 4 | own run | I08, I13, G23 |
| 7 | 4 | FT-04 | A review check that names its element set, in a real run (T-42) | whether D62 ends the three-grain drift of run 12 | 4 | 1 | 7 | next run | G29 |
| 8 | 18 | FT-19 | Evidence audit under D64 on a record with superseded rows (T-43) | that the audit stops grading history | 2 | 1 | 3 | next run | G30, G22 |
| 9 | 5 | FT-05 | Second graph-vs-direct pair on a prose task (T-44) | whether the 16× and the 1-vs-4 generalise beyond one code task | 5 | 5 | 5 | pair | G28, G25, G26 |
| 10 | 10 | FT-11 | Reserve exhaustion by a non-audit run at the wall | X30 at the boundary; the lead's stop-or-raise decision | 3 | 1 | 5 | own run | I10, G18 |
| 11 | 2 | FT-02 | Resume from the record alone: a fresh lead gets only the run directory and 'resume' | the record-is-the-state claim (D55); what a lead silently carries in its head | 5 | 2 | 8 | own run | I11 |
| 12 | 11 | FT-09 | Codex as lead on a full run with prompt v3.5.1 | whether the rules hold for a lead that is not the author | 4 | 4 | 4 | pair | G31, I17 |
| 13 | 17 | FT-17 | Dissent path: the same section fails twice with 'cannot address' | the accepted-with-both-positions outcome | 3 | 3 | 3 | own run | G10, G15 |
| 14 | 19 | FT-20 | One-node graph | the 'one node is a valid graph' floor | 2 | 1 | 3 | heuristic skip | G02 |
| 15 | 20 | FT-21 | Reviewer returns a fix → void | R45 enforcement | 2 | 1 | 3 | heuristic skip | I05 |
| 16 | 21 | FT-22 | Scope-violation write caught before the gate | D55 exclusivity | 2 | 1 | 3 | heuristic skip | I03 |
| 17 | 23 | FT-24 | Planted label leak: does the lead's pre-dispatch check catch it | D65 as a habit, not a rule | 2 | 1 | 3 | heuristic skip | I07 |
| 18 | 24 | FT-25 | An inspect gate on a real node | the third gate type, never used | 2 | 1 | 3 | heuristic skip | G05 |
| 19 | 26 | FT-27 | A fail resting on a property outside fails_when, and a ruling-based fail, both voided | the two void rules never exercised | 2 | 2 | 2 | heuristic skip | G13, G14 |
| 20 | 13 | FT-13 | Cause (d): a planted source defect | the block-until-a-person path | 3 | 2 | 4 | own run | G04 |
| 21 | 6 | FT-06 | Reviewer repeatability: the same brief and pair three times per tier | how much of a verdict is the reviewer and how much is the artifact | 4 | 3 | 5 | own run | G27 |
| 22 | 7 | FT-07 | Cause (b): plant a wrong field in an accepted upstream and let a downstream gate find it | the only return path that reopens an accepted node | 4 | 3 | 5 | own run | G08 |
| 23 | 29 | FT-26 | Escalation 2: two cause-(a) fails on a sonnet node → opus, capped | the cap at the top tier | 2 | 3 | 1 | heuristic skip | G07 |
| 24 | 25 | FT-18 | Mixed prose + code task in one graph | whether the gate vocabulary spans both kinds in one record | 3 | 4 | 2 | pair | G01 |
| 25 | 27 | FT-28 | Nine-plus node diamond with a re-gate on the join | D59 under two fan-ins on one path | 3 | 5 | 1 | heuristic skip | G03 |
| 26 | 28 | FT-29 | A human as lead | whether the prompt is followable without the author's habits | 3 | 5 | 1 | heuristic skip | G24 |
| — | 8 | FT-08 | Independent re-triage: a second lead re-grades one record's observations from the record alone | the silent-lead-error class (the C12 triage) | 4 | 3 | 5 | own run | I17 |
| — | 16 | FT-16 | Opus reviewer vs sonnet on one mutant set | whether tier buys reviewer sensitivity | 3 | 3 | 3 | own run | none open (G06 is covered; this measures what the opus tier adds, not whether it was used) |
| — | 22 | FT-23 | Partial-output builder → attempt counted, hypothesis recorded | layer 6 bookkeeping | 2 | 1 | 3 | heuristic skip | I01, I02 |

Open conditions no test closes: I15 (Subagent token or context exhaustion mid-write). Tokens and time per run are a recording practice for every run rather than a test.

## 5. Folded into the next graph run (run 13)

At little marginal cost: FT-03 (LIMIT wall — set LIMIT below the graph's minimum on a small run), FT-01 (a builder brief that forbids running the gate; the lead's rerun must catch it), FT-10 (stop one builder on purpose and replay from next_action), FT-04 (T-42: every removal check names its element set), FT-19 (T-43: audit samples newest rows), FT-15 (negative validator fixtures, as kit work before the run). FT-02 (resume from the record alone) is the first own-run test: hand run 13's record to a fresh lead mid-run.
