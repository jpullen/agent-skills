# Calibration log — graph-prompt

Tracks every decision made during calibration runs, the finding it rests on, and the future test it implies. Run records are the author's private working records and are not published; this file is the cross-run ledger.

Legend: **D-xx** decisions taken in a run · **F-xx** prompt findings · **T-xx** future tests implied

Runs 5 and 7–10 are published as results only; their task text is not included.

---

## Run 1 — v2.6, task: template tooling

### Decisions

| id | decision | rests on | impact on future tests |
|---|---|---|---|
| D-01 | Deliverable scripts live in `{{OUTPUT}}/code/`, not `{{RUN_DIR}}/code/` | F-03 | T-03 |
| D-02 | "Green at baseline → rewrite or drop" applied per gate (test file), not per test case | F-01 | T-01 |
| D-03 | Lead wrote no-op stubs to convert `not run` into assertion-red | layer_5 exec rule | T-02 |
| D-04 | Integration C4 reuses g3's review verdict when README content hash unchanged | F-02; approved 23:07 | T-04 |
| D-05 | Hold the planted fixture defect; deliver v2.6 as `partial`; run v1 on identical inputs; then extend scope, fix, resume under the sources-differ override | comparison needs identical inputs | T-05, T-06, T-07 |
| D-06 | Run both audits on a partial delivery even though the integration node never ran | spec silent on audits under partial; cheap; calibration data | T-08 |
| D-07 | Record corrected (integration row added) but F-07 rows left non-conforming rather than given a false isolation value | layer_7 "corrects the record, never the verdicts" | T-11 |

### Findings

| id | finding | layer |
|---|---|---|
| F-01 | Green-at-baseline rule does not say whether it applies per case or per gate; per case it deletes positive-case tests | principles, layer_5 |
| F-02 | Spec silent on re-reviewing a byte-identical artifact at integration | layer_7 |
| F-03 | `{{RUN_DIR}}/code/` conflicts with `{{OUTPUT}}` when scripts are the deliverable | layer_3 |
| F-04 | `{{LIMIT}}` counts node runs; lead work (framing, graph, gate tests, baseline, stubs) counts zero | inputs, execution_loop |
| F-05 | Triage causes (a)–(d) have no case for a defective `{{SOURCES}}` input; correction edge has nowhere to send the unit | layer_6 |
| F-06 | Spec does not say whether audits run on a partial delivery | layer_7 |
| F-07 | checks.md has no row state for a review gate that has not yet run; `fresh subagent — <pending>` is non-conforming by the record's own rules | layer_5 |

### Observations (not yet findings)

- O-A: haiku passed both code-node gates first attempt; g2's one failure was the source, not the builder. Tier rule's lowest-tier default held for parser-class work. (n=2)
- O-B: a builder on haiku, given a gate test it could not edit, reported a source defect rather than weakening the check or editing the fixture. The structural guard (may-not list + lead-owned tests) was not tested against pressure; the builder simply complied. (n=1)
- O-C: the planted defect was caught by a lead-written spec-rule test (W7 name-match) that no fixture and no `{{CHECKS}}` item exercised. `{{CHECKS}}` alone would have let it survive.

### Future tests implied

| id | test | answers | preconditions |
|---|---|---|---|
| T-01 | Same task with the green-at-baseline rule applied per test case | does the per-case reading delete positive tests and produce a reject-everything validator that passes C2/C3? | v2.7 wording decision |
| T-02 | A code node whose baseline red is reachable without a stub (existing module, missing function) | is the stub rule ever needed when the module exists, or only on greenfield? | different task |
| T-03 | A task where scripts are run machinery, not the deliverable | does `{{RUN_DIR}}/code/` placement hold when D-01's reason is absent? | different task |
| T-04 | Same task, literal reading: fresh second review at integration on unchanged README | do two independent reviewers ever disagree on a byte-identical artifact? (D1 vs cost) | resume of run 1 |
| T-05 | **v1 on identical inputs** (same fixtures incl. the plant, same `{{CHECKS}}`) | does v1's process surface the name-match defect, ship a validator that calls clean clean, or silently edit the fixture? | run 1 delivered partial first |
| T-06 | Resume run 1 under the sources-differ override after fixing the fixture | does the handoff layer resume from `Next action` without rerunning g1? does g2 re-gate without a builder rerun? | T-05 complete |
| T-07 | Add a triage cause (e) `source defect` to v2.7 and rerun a planted-source task | does the correction edge route to a scope/blocker decision instead of stalling? | v2.7 |
| T-08 | Partial delivery with audits skipped vs run | does the evidence audit on a partial record change what gets delivered? | compare D-06 against a skipped-audit run |
| T-09 | Same task, `{{MODE}}: autonomous` | does the lead block at O-01 and deliver partial without asking, as layer_4 and inputs specify? | after v1 comparison |
| T-11 | Add isolation value `not run` to v2.7; rerun run 1's record through wellformed.py | does the record format support a partial run without lying? | v2.7 |
| T-10 | Plant a defect in a `{{SOURCES}}` file the builder reads but the gate test does not touch | does anything catch a source defect that no spec rule covers? (lower bound on O-C) | new plant |

### Run 1 result (sealed file opened at delivery)

Planted: `clean/graph.md` n3 `reads: n2: descriptions, constraints` → `descriptions, rationale`; violates layer_1 name-match. Planter's prediction: both scripts exit 0 — true for a five-category validator. Outcome: caught at the g2 gate by the lead-written W7 test; the haiku builder reported it rather than editing the fixture or weakening the rule; the lead could not fix it (out of scope) and could not route it (F-05) and delivered partial. The planter's "both scripts exit 0" prediction was false for the scripts actually built, because the gate test demanded the spec rule. O-C stands: the catch came from test-first spec rules, not from `{{CHECKS}}`.

Run 1 numbers: 4 node runs of 30; builders haiku ×2 (1 pass, 1 fail-on-source); audits 2; subagent tokens ≈ 284k excluding setup. Deliverables: both scripts, both gate tests, integration.sh. Not delivered: README.

## Run 2 — v1 (opus designer, depth-1, P-03), same task, same inputs

### Design-phase result (before any builder ran)

**R2-1 — The v1 lead found the planted defect and designed it out.** Its baseline inspection located `clean/graph.md:34` (n3 reads `rationale`; n2 has no such section) and identified the v2.6 name-match rule it violates. It then reasoned: C1 requires exit 0 on clean, therefore no script may implement that rule. Both builder briefs carry an explicit prohibition: "The reads/shape name-match between graph.md nodes. The clean fixture's graph.md has such a mismatch, and every script must still exit 0 on clean" (in both builder briefs, which are not published). The lead surfaced the finding in its report as a "key finding" — it did not hide it — but treated `{{CHECKS}}` as senior to the spec and bound its builders to the fixture.

Under v2.6 the same defect produced a gate failure attributed to `{{SOURCES}}` and a partial delivery (run 1, O-01). Under v1 it produces a complete delivery of validators that are correct on every fixture and silent on the spec rule the fixture violates. Same inputs, same defect, opposite outcome, and the divergence is entirely in the design phase: v2.6's lead wrote the spec rule into the gate test before dispatch because test-first + "fails when" demanded a spec-grounded check; v1's lead wrote fixture-grounded checks because `{{CHECKS}}` was the only stated authority.

This is T-05's answer to "does v1 ship a validator that calls clean clean": yes, by design, with the defect known and documented.

**R2-2 — An opus lead under v1 reproduced most of v2.6's machinery unprompted.** 31 lead-written gate tests before any builder, a stub-based baseline run three ways (no scripts / always-pass stub / always-fail stub) to show every test can fail, a scope-violation detector, a README structure checker, backups, a learned-rules section. v1 asks for none of this explicitly. Confound for the comparison: a capable lead supplies test-first and discriminating checks on its own; v2.6's contribution on those points may be smaller than run 1 suggested, and its distinct contribution is the *authority ordering* (spec over checks, source defects as blockers) that no amount of lead capability supplied here. Needs a lower-tier v1 lead to separate (T-12).

**R2-3 — v1 lead also found C2/C3 half-green at baseline** (a missing script exits 2, which is non-zero) and tightened its gate tests to require exit 1 plus the exact first line. v2.6's lead (run 1) did not notice this. Finding for the v2.6 integration script: C2/C3 as written accept exit 2. F-08.

### Future tests implied

| id | test | answers | preconditions |
|---|---|---|---|
| T-12 | Run 2 again with a sonnet or haiku designer under v1 | is R2-2's machinery a property of opus or of any lead? isolates what v2.6 adds beyond capability | after run 2 completes |
| T-13 | Run 1's task under v2.6 with `{{CHECKS}}` deliberately contradicting the spec (as here) and a lead on sonnet | does v2.6's authority ordering hold on a weaker lead, or does the lead follow CHECKS as v1's did? | v2.6 unchanged |

### Findings

| id | finding | layer |
|---|---|---|
| F-08 | run 1's integration.sh accepts any non-zero exit for C2/C3; a missing script satisfies the exit condition | layer_7 (run 1 implementation, not the prompt) |

### Run 2 result — delivered complete

v1 delivered `complete`: 5/5 nodes accepted first attempt, C1–C5 pass, 21/21 checks.md rows pass, 11 of 30 node runs (3 subagent dispatches: sonnet, sonnet, haiku; 8 code/gate runs). One process failure (designer's gate command pointed `--basetemp` at a nonexistent parent; fixed by the designer, no attempt charged). Designer reported the plant as O3 ("neither script checks this, by design") and left it open. Designer also found O9, a parsing divergence between the two scripts that no gate covers, and declined to tighten the check after the fact.

### T-05 comparison — same task, same inputs, same plant

| | run 1 (v2.6, fable lead) | run 2 (v1, opus lead via P-03) |
|---|---|---|
| status | partial | complete |
| node runs | 4 | 11 |
| subagent tokens (harness) | ≈284k | ≈1,130k (designer 240k cumulative + builders 265k) — not comparable; designer was resumed 5× |
| builders | haiku, haiku | sonnet, sonnet, haiku |
| lead-written gate tests | 34 | 42 |
| plant found | yes, by g2 builder at gate | yes, by lead at baseline |
| plant outcome | gate fail → source blocker → partial | documented, designed around → complete |
| README | not produced | produced, gated |

**Rule-coverage measurement** (one defect per spec rule injected into a repaired clean record; "caught" = either script exits non-zero):

| spec rule | v2.6 scripts | v1 scripts |
|---|---|---|
| verdict case (`Pass`) | caught | caught |
| wrong column count | caught | caught |
| evidence `none` with `pass` | caught | missed |
| exec row with review isolation | caught | missed |
| degraded review marked `pass` | caught | missed |
| check type outside set | caught | missed |
| missing required node field | caught | missed |
| kind outside set | caught | missed |
| judgment node without tier rule | caught | missed |
| split reason outside set | caught | missed |
| reads names unknown node | caught | missed |
| reads/shape mismatch (the plant) | caught | missed |
| **total** | **12/12** | **2/12** |

Both script sets pass every `{{CHECKS}}` item identically on the five defect fixtures. The ten-rule gap is invisible to `{{CHECKS}}`; it is visible only to the spec.

**Interpretation.** v1 optimized to the acceptance checks and delivered exactly what they asked for, faster, with a README, and with the plant honestly reported as out of scope. v2.6 optimized to the spec the checks were derived from, caught the plant as a source defect, could not resolve it within scope, and delivered partial without a README. On the dimension `{{CHECKS}}` measures, v1 wins. On the dimension the task actually needed — validators that implement the record spec — v2.6's scripts implement 12 rules and v1's implement 2, and v1's lead knew about at least one of the missing ten and chose `{{CHECKS}}` over it.

The mechanism, as far as one run each can show: v2.6's `fails when` + test-first obligations pushed the lead to derive checks from the spec; v1's "fixed evaluator" + `{{CHECKS}}` as the only stated authority pushed the lead to derive checks from the fixtures. Neither prompt told its lead which was senior. v2.6's lead inferred spec-senior from the shape of the obligations; v1's lead inferred checks-senior from the absence of any other authority. **The missing rule in both prompts is an explicit authority ordering between `{{CHECKS}}` and `{{SOURCES}}`-stated specs.** F-09.

**What this does not show.** n=1 per arm; different lead models (fable vs opus); different lead positions (depth 0 vs depth 1). R2-2 stands: an opus lead supplied test-first, discriminating baselines, and scope checks under v1 without being asked, so the coverage gap is not "v1 lacks test-first" — it is "v1 gives the lead no reason to look past `{{CHECKS}}`." T-12 (weaker v1 lead) and T-13 (v2.6 with a weaker lead and contradicting checks) are the tests that separate prompt from lead.

### Findings

| id | finding | layer |
|---|---|---|
| F-09 | Neither prompt states the authority order between `{{CHECKS}}` and a spec in `{{SOURCES}}`; each lead inferred a different one and the outcomes diverged entirely on that inference | inputs |
| F-10 | v1's designer, as a resumed subagent across 5 turns, accumulated ≈240k tokens; the P-03 protocol's cost is the designer's growing context, not the dispatcher's | protocol |

### Decisions

| id | decision | rests on | impact |
|---|---|---|---|
| D-08 | v1's deliverable left as delivered; O9 and O3 not fixed; cache dirs removed by the designer (its D11) | comparison integrity | T-06 resumes v2.6, not v1 |

### Future tests (added)

| id | test | answers | preconditions |
|---|---|---|---|
| T-14 | Add to both prompts: "`{{CHECKS}}` are necessary; a spec named in `{{SOURCES}}` is also binding; a conflict between them is a blocker, not a design constraint." Rerun both arms. | does the authority rule alone close the 10-rule gap under v1? | v1.1, v2.7 |
| T-15 | Run v1 with `{{CHECKS}}` expanded to name the spec rules explicitly (12 items instead of 5) | is the gap closable by better checks alone, without changing the prompt? | same fixtures |

## Run 1 resumed (T-06) — v2.6 — delivered complete

Handoff layer exercised as written: new `{{RUN_DIR}}`, Decisions entry naming the changed source, g1 carried, g2 re-gated on its saved artifact (16/16, hash unchanged) with no builder rerun. g3 built on sonnet, review gate with a W7-removed mutant in random A/B order: reviewer failed A (mutant) with the searched-for string `- W7:` as its anchor, passed B. Integration exec items all pass; C4 carried under D-04 (hash equal). Well-formedness audit exit 0 on the run's own record (F-07 rows resolved by real ids). Evidence audit 0/7 miscited. Template saved.

Totals across run 1 + r2: 11 node runs of 30; builders haiku ×2, sonnet ×1; reviewers/auditors sonnet ×3; zero correction-edge retries; one block on a source defect.

**T-06 answers:** resume worked from `Next action` without rerunning accepted nodes — yes. g2 re-gated without a builder rerun — yes. Cost of the resume itself: one code run.

**Comparison update, final deliverables side by side:**

| | v2.6 (run 1 + r2) | v1 (run 2) |
|---|---|---|
| node runs | 11 | 11 |
| spec rules implemented | 12/12 | 2/12 |
| `{{CHECKS}}` | 5/5 | 5/5 |
| README | yes, review-gated with mutant | yes, structure-script-gated + lead inspect |
| retries | 0 | 0 |
| blocks | 1 (source defect, resolved by person) | 0 |
| open issues at delivery | F-08 (integration.sh exit check loose) | O9 (parser divergence between scripts), O3 (the plant, by design) |

Same node-run count. v2.6 needed one human decision v1 did not; v1 shipped two known defects v2.6 did not have.

### Observations (added)

- O-D: the review gate with a random-order mutant produced a reviewer verdict with a verbatim absence anchor on the first try. The mutant construction (remove one `fails when` property) was mechanical here because the README's Checks section is a list; it would be harder on prose. (n=1)
- O-E: both evidence auditors (run 1 and r2) returned 0% miscited and both volunteered an observation outside their rows. Neither observation was wrong. The sequestration held on *inputs*; it did not confine *outputs*. Whether to treat extra-brief observations as noise or as a free second review is a v2.7 question. (n=2)

## Run 3 — v1.1 (T-14), same task, same inputs, plant restored

v1.1 = v1 + one line in `<inputs>`: "{{CHECKS}} are necessary, not sufficient. A specification named in {{SOURCES}} is also binding on the deliverable. If a check and a specification conflict, that conflict is a blocker to report, not a constraint to design around." Nothing else changed. Opus designer, P-03 protocol, fresh context.

Predictions, written before the designer returned:
- P-A: the designer finds the plant (as both prior leads did).
- P-B: with the authority line, it reports the C1/spec conflict as a blocker at the approval pause instead of forbidding the check in the briefs.
- P-C: if P-B holds, its gate tests cover more than 2 of the 12 spec rules — the line changes what the lead derives checks from.
- P-D: if P-B fails (designer still designs around it), the structure in v2.6 is doing the work, not the authority line, and v2.7 should be v2.6-based.

### Run 3 design-phase result (against the pre-registered predictions)

- **P-A (finds the plant): true.** Located `clean/graph.md:34` and the name-match rule. Also inferred from file mtimes (clean/graph.md 21:45, same minute as inputs.md; all other fixtures 10-31) that FIXTURES.md's "planted defect: none" was stale. The plant leaked through filesystem metadata — protocol note P-04.
- **P-B (reports conflict as blocker, not design constraint): partially true.** The "ask one focused question" clause fired for the first time in three runs. The designer did not forbid the name-match check in its briefs. It framed two readings — A: scripts implement only the five layer_7 audit lines, no conflict, README documents the gap under `## Not checked`; B: scripts implement the v2.6 record format generally, C1 conflicts with the spec, blocker, fixtures out of scope — built the graph under A, and stopped to ask which the person wants. v1 silently chose A and bound its builders to it; v1.1 surfaced A vs B and asked. The line moved the lead from *design around* to *surface and ask*. It did not move it to *block*; it chose the non-blocking reading as the default and asked for permission to proceed under it.
- **P-C (gate tests cover more spec rules): false under Reading A.** gates.py check ids: CR0–CR3, WF1–WF2 — the same five audit lines plus a file-presence check. 2/12 spec rules, same as v1. Under Reading B the designer says it cannot proceed. So the line did not change what checks the lead derived; it changed whether the lead told anyone about the conflict.
- **P-D: not triggered** (P-B did not fail outright). Mixed result: the authority line buys disclosure, not coverage. The structure that produced 12/12 under v2.6 — `fails when` per check, test-first against the spec — is what produced coverage, and v1.1 does not have it.

**New finding from the v1.1 designer, verified:** every fixture, including clean, violates v2.6 layer_3 ("Every code node spec lists `command:`, `expected exit:`, `rules:`, and `gate:`") — the fixtures' code nodes have none of the three — and review-only n2 lacks the layer_5 `exec/inspect unavailable:` line. My run-1 W3 required-field list (11 fields) also omits `command:`, `expected exit:`, `gate:`, so v2.6's "12/12" is 12 of the rules I tested for, not 12 of all rules in the spec. **F-11**: the fixtures are not spec-clean on rules neither run tested, and the author of both the fixtures and the v2.6 gate tests (me) missed the same rules in both. The v1.1 designer, reading the spec cold, found them.

**Other v1.1 design choices worth noting:** all gates deterministic code (no review node at all — the README gate checks id and term presence, not prose correctness, and the designer said so); a separate N3 node that writes black-box tests which must not import the scripts; a self-test showing every gate can pass and fail against oracle stubs; 10 planned runs; added S1 (wellformed must also flag d2/d3/d5) as its own extension of `{{CHECKS}}` from the spec — which is exactly the authority line working, on a rule that doesn't conflict with a fixture.

### Run 3 closed — Reading B (Jeremy, 22:14), blocked at approval

0 of 30 node runs. Blocker statement named three spec violations in `clean` (name-match at :34; layer_3 code-node fields absent on n1/n3/integration; layer_5 `exec/inspect unavailable:` absent on n2), the latter two in all six fixtures. Three unblock paths offered: repair fixtures, revise C1/C2, extend scope. One new consequence: **C2's expected ids are wrong under a spec-conformant validator** — in d1 and d4 the first failure in record order is n1's missing layer_3 fields at line 3, not n3/n2. So `{{CHECKS}}` C2 encodes the five-audit-line reading; a full-spec validator cannot satisfy C2 as written even on repaired d-fixtures unless the systematic violations are repaired too. F-13.

Three-arm result on identical inputs, same plant:
| arm | found plant | at | action | delivered |
|---|---|---|---|---|
| v2.6 | yes | g2 gate (builder) | blocked; source defect, out of scope | partial → complete after human scope extension |
| v1 | yes | baseline (lead) | designed around; briefs forbid the check | complete, 2/12 rules |
| v1.1 | yes | baseline (lead) | surfaced A/B, asked; under B: blocked at approval | blocked, 0 runs |

### Findings (added)
| id | finding | layer |
|---|---|---|
| F-13 | `{{CHECKS}}` C2/C3 expected node ids assume the validator checks only five rules; under full-spec validation the first record-order failure is a systematic fixture defect, not the planted one. The acceptance checks themselves encode Reading A. | inputs (task design) |

### Decision pending (Jeremy) — resolved

Reading A or Reading B for run 3. A delivers a complete run with the gap documented; B blocks at approval exactly as v2.6 blocked at gate. For the comparison, B is the honest reading of the authority line ("a specification named in {{SOURCES}} is also binding") and A is the reading that lets the run finish.

### Findings (added)

| id | finding | layer |
|---|---|---|
| F-11 | Fixtures and the v2.6 W3 test both omit layer_3 code-node fields (`command:`, `expected exit:`, `gate:`) and the layer_5 `exec/inspect unavailable:` line; found by a cold read of the spec, not by any test | fixtures, run-1 gate test |
| F-12 | The authority line produces disclosure of a checks/spec conflict but not spec-derived checks; coverage came from `fails when` + test-first, which v1.1 lacks | inputs vs layer_1/5 |

## Independent conformance audit (opus, fresh context, spec + fixtures only)

Checklist derived from the spec: **89 rules** (graph.md 32, checks.md 22, progress.md 22, cross-file 13). My run-1 gate tests covered 12. The 12 are a subset of the 89; nothing I tested was wrong, but 77 rules had no test.

Fixture audit: no fixture is clean. **14 rules violated by all six** (systematic — mine, not planted): clear G-24 (code-node `command:`/`expected exit:`/`gate:`), G-28 (review-only `exec/inspect unavailable:`), X-03 (graph.md check text ≠ checks.md row with no Decisions entry); probable C-19, C-10; nine contestable. Every planted defect confirmed accurate per FIXTURES.md. Per-fixture totals 15–20 violations each, of which 1 is the planted one.

**19 ambiguities in the spec itself**, each with the conflicting passages cited — among them: the brevity allowance forbids `None` on fields the spec itself gives `None` values to; "run record" and `## Subagents` are never defined; `none` is absent from the red-evidence list but implied legal elsewhere; `Enforcement` is a "line" in one place and a section in another; `Isolation` is required on every audit but neither permitted value fits a script; the well-formedness code node's membership in graph.md is self-referential; `tier rule:` is undefined when no line fires; exec evidence wants exit codes in layer_5 but the row format asks only for an output excerpt.

### What this changes

- **The 12/12 vs 2/12 measurement stands as stated** (12 of the rules I tested) but is 12/89 vs 2/89 against the full derived checklist, and most of the 89 are untested in both. The ratio between arms holds; the absolute coverage claim does not.
- **Fixture repair against an ambiguous spec reproduces the correlated-error problem** (F-11): I would resolve each ambiguity my way, write fixtures to it, and test to it. The 9 contestable systematic violations are contestable *because* the spec is ambiguous there. Repairing them now would encode my readings as ground truth.
- **Therefore order changes:** v2.7 first (resolve the 19 ambiguities in the spec text, one decision each, recorded), then fixtures repaired against the disambiguated spec by a different author than the one who writes the tests, then re-measure.
- The 5 clear+probable systematic violations (G-24, G-28, X-03, C-19, C-10) are unambiguous and can be repaired now without pre-empting v2.7. F-14.

### Findings (added)
| id | finding | layer |
|---|---|---|
| F-14 | The spec has 19 internal ambiguities, each of which a validator author must silently resolve; two independent authors (me, the auditor) resolved several differently. A spec that governs validators needs a single reading per rule before any fixture is "clean". | whole prompt |
| F-15 | The well-formedness audit's own 5 lines (layer_7) cover 5 of 89 derivable rules; the audit as specified is a smoke test, not a conformance check | layer_7 |

### Future tests (added)
| id | test | answers | preconditions |
|---|---|---|---|
| T-16 | After v2.7 disambiguation: a second independent auditor derives the checklist again; compare rule counts and per-rule wording with this one | did disambiguation converge the derivation? (two cold readers agree) | v2.7 |
| T-17 | Repair fixtures (different author than tests); rerun v2.6/v2.7 and v1/v1.1 script sets against a per-rule defect injection over the full checklist | true coverage of each arm's validators | T-16 |

## v2.7 written (2026-11-02)

Files of that version: `graph-prompt-v2.7.md` (4,030 words, +18% over v2.6) and `graph-prompt-background-v2.7.md` (D27–D33 added) are unpublished kit files; `graph-prompt-rulings.md` (19 ambiguity rulings + 11 finding fixes + vocabulary, each with its prompt location) ships in its current form at `plugins/graph-prompt/skills/graph/references/graph-prompt-rulings.md`. All 30 rulings (19 + 11) grep-verified present [the v2.9 rulings added to the same file are numbered from R20; see L490]; no v2.3-era self-monitoring text.

Size note: the prompt grew again. D13's shrink hypothesis is now disconfirmed three versions running; the honest statement is that every calibration finding added an obligation and none removed one. T-18: after the next run, list every obligation that did not fire and cut candidates from that list.

What v2.7 does NOT do: repair the fixtures (waits for T-16's second derivation so fixtures are written against a converged rule list); re-measure coverage (T-17, after fixtures); re-run the prior-art check on new vocabulary (the four adopted terms were already verified).

### Next in order
1. T-16: second cold derivation of the rule list from v2.7 by a fresh opus reader; compare with the 89-rule list. Convergence threshold: < 5 rules different.
2. Fixture repair by a non-test author against the converged list; the five clear systematic defects first.
3. T-17: re-measure v2.6/v2.7 and v1/v1.1 script coverage over the full rule list.
4. First v2.7 run on a task that is not its own tooling.

### Future tests (added)
| id | test | answers | preconditions |
|---|---|---|---|
| T-18 | After one v2.7 run, enumerate obligations that never fired; cut the prompt to the ones that did and rerun | which of 4,030 words are load-bearing? | one v2.7 run |

## T-16 — second cold derivation, from v2.7 (pre-registered)

First derivation (from v2.6): 89 rules, 19 ambiguities. Convergence criteria, written before the second result arrived:
- C-a: ambiguity count ≤ 5 (v2.7 ruled on 19; new ones from new material — rules.md, cause (e), `not run` — are expected and acceptable up to 5)
- C-b: of the 19 original ambiguities, ≤ 2 re-reported in any form
- C-c: rule count for graph.md + checks.md + progress.md within ±10 of the first derivation's 76 (32+22+22), allowing for v2.7 additions
- C-d: no new ambiguity that a v2.7 ruling introduced (a ruling that created a conflict with another passage)
Pass = C-a, C-b, C-d all hold. C-c is informational.

### T-16 result — FAIL on all three pass criteria

Second derivation (opus, cold, v2.7 only): **152 rules** (framing 9, graph 39, checks 35, progress 30, rules.md 5, lessons 4, cross-file 30), **75 ambiguities**.

- C-a (≤ 5 ambiguities): **fail**, 75.
- C-b (≤ 2 of the original 19 re-reported): **fail**. Re-reported in some form: red-evidence `none`/`minimal — inspect` vs the red-case rule (#9–11); isolation on non-review rows (#17); integration node's membership in graph.md (#33); one check vs two per node (#25); node-state lists inconsistent (#46); Decisions entry formats (#49); well-formedness as self-referential (#56). At least 7.
- C-c (graph+checks+progress within ±10 of 76): informational, 104 — the spec grew and the reader was more exhaustive.
- C-d (no ambiguity introduced by a ruling): **fail**. Rulings that created new conflicts: `exercises:` has no column (#3); `carried from` has no column (#5); summary-row red evidence not a permitted value (#6); well-formedness line omits the new `not run` isolation (#18); void-rerun attempt numbering (#23); cause (d) tier bump breaks the tier-rule computation (#30); DoD says `isolation: fresh subagent` without the required id (#55). Seven, each traceable to a v2.7 edit.

D32's hypothesis (two readers differ by < 5 rules) is disconfirmed by a wide margin.

### Interpretation

The 75 are not uniform. Roughly: **~30 are "no format given"** (graph.md has no overall syntax; `## Graph` has no line format; lessons.md has fields but no syntax; rules.md id format; Open issues format; how retries appear in graph.md; `guarded by:` syntax) — the spec names fields and never gives a grammar. **~20 are passage conflicts** (two sections disagree). **~15 are undefined terms** ("run file", "contradicts", "case", "accepted result", split-reason terms). **7 were created by v2.7 rulings.**

The mechanism: every ruling adds a format rule, every format rule is one more surface that can conflict with another, and the number of pairwise surfaces grows faster than the number of rulings. v2.6 → v2.7 added ~20 rulings and ~600 words and the ambiguity count went 19 → 75. A third round would ruling on 75 and produce more. **The record format is being specified in prose, and prose does not converge on a grammar.** F-16.

The ~30 "no format given" items are one finding, not thirty: the record needs a schema. A schema (JSON Schema, or a small grammar for the markdown forms) is unambiguous by construction, is validated by an existing validator rather than a derived checklist, and makes the well-formedness audit a one-line call. The prompt then *references* the schema instead of *restating* it, and the prose shrinks instead of growing. This is the same move the Guide's two-file split made for rationale, applied to format.

The ~20 conflicts and ~15 undefined terms would mostly disappear with a schema too — most conflicts are between a prose restatement and a list, and a schema has one source.

### What this does to the plan

- Fixture repair against v2.7 prose is off: 75 open readings, 7 of them mine.
- v2.8 by prose ruling is off: the evidence says it would not converge.
- **The next version factors the record format out of the prompt into a schema file** (`graph-record.schema.json` or equivalent), with the prompt reduced to behavior and the schema carrying every field, value list, and cross-reference. The well-formedness audit becomes schema validation plus the handful of cross-file checks a schema cannot express (name-match, hash equality, subagent-id presence). The second-derivation test then applies to the schema: two readers of a schema should produce identical rule lists, which is the convergence criterion stated properly.
- Fixtures are then generated from the schema, not hand-written — which removes the correlated-error problem at its source.

### Findings (added)
| id | finding | layer |
|---|---|---|
| F-16 | Disambiguation by prose ruling diverges: 19 → 75 ambiguities across one round, 7 created by the rulings themselves. The record format needs a schema, not more rules. | whole prompt |

### Future tests (added)
| id | test | answers | preconditions |
|---|---|---|---|
| T-19 | Write `graph-record.schema.json`; have two cold readers derive rule lists from the schema alone; compare | does a schema converge where prose did not? threshold: identical field/value lists, ≤ 2 differences in cross-file rules | schema written |
| T-20 | Generate fixtures from the schema (one valid, one per violated constraint); run v2.6/v2.7/v1/v1.1 script sets against them | true coverage, with ground truth that no human hand-wrote | T-19 |

## Schema written (2026-11-03)

`graph-record.schema.json` (420 lines, 51 conditionals), `validate.py` (227 lines, X01–X20), `example/` (run-1 record in YAML, validates clean), README. Mutation test 22/22 caught, including the plant (X02). Two protocol notes from the mutation run: YAML coerces an all-digit subagent id to int (schema caught it as a type error, not as the intended X05 — quote ids); a mutation can be caught by an earlier rule than intended (X01 before X13) — mutation tests must isolate one rule each.

Resolved by structure rather than ruling, from the 75: #1/#2 (hypotheses section, one cause enum), #3 (`exercises` on acceptance rows), #5 (`carried` evidence kind), #6 (`checks_baseline` red-evidence kind), #15 (mutant record fields), #17 (isolation per type via conditionals), #18 (`not_run` everywhere, forces `unresolved`), #23 (attempt is an integer on every row), #29/#30 (tier_rule list + escalations count, X08 arithmetic), #33 (integration is a row subject kind, not a node), #37 (reads = {sources, upstream}), #38 (`unavailable` is a node field), #40 (`guarded_by` object), #42 (assumptions have `assumed` in every mode), #44 (blocked is a progress.graph list), #46 (one state enum, X10 partition), #49 (decision kinds), #51 (subagent role enum), #52 (audit verdict is its own enum), #55 (evidence audit isolation object), #58 (open issues have ids), #66 (not-started nodes still need an attempt-1 row — X01; red evidence `not_run`), #67 (attempt on every row). Roughly 30 of 75 closed by having a grammar at all; the rest need a prompt pass (next).

### Future tests (status)
- T-19 ready: two cold readers derive rule lists from the schema; convergence criterion is identical field/value lists.
- T-20 ready: generate fixtures from the schema (valid + one per constraint) rather than by hand.

### Next
1. v2.8 prompt: replace layers 1/5/6/7 field and value lists and the handoff section list with references to the schema; keep behavior only. Expected size: well under v2.6.
2. T-19.
3. T-20, then re-measure all four script sets.

## v2.8 written (2026-11-03) — format by reference

`graph-prompt-v2.8.md`: **2,780 words** [the CHANGELOG and background record v2.8 as 2,831 and v2.9 as 2,933 words; this log's counts were taken at the time, and the two are not reconciled here], −31% from v2.7, −19% from v2.6. First shrink in the series. Every behavioral obligation retained (grep-verified: authority, SoD, stub rule, mutant procedure, cause (e), cannot-address, hash-carried verdicts, rules.yaml, validate.py, proven ban, auditor notes, 7 "applies in all contexts"). No row format, field list, verdict table, or permitted-value list restated (grep: 0). D13's shrink hypothesis, disconfirmed three times by prose rulings, holds under factoring: the prompt shrinks when the format leaves it.

## T-19 — two cold readers of the schema (pre-registered)

Readers A and B (opus, fresh, schema file only, identical brief, run in parallel). Criteria:
- C-a: field inventories identical in count per file (±0).
- C-b: conditional-rule counts identical; wording may differ.
- C-c: cross-file restatements agree on every X-id.
- C-d: ambiguity count ≤ 3 per reader, and no ambiguity reported by both that names a two-readings conflict (an absent-constraint note is acceptable).
Pass = all four. This is the convergence test prose could not pass (19 → 75).

### T-19 result

| | reader A | reader B |
|---|---|---|
| fields (graph/checks/progress/framing/rules/lessons) | 43/43/69/21/7/8 | 43/43/69/21/7/8 |
| conditionals | 51 | 51 |
| cross-file | 20, X01–X20 | 20, X01–X20 |
| ambiguities | 75 | 68 |

- **C-a pass**: field inventories identical, per file, to the item. (A counted each file's root line; nested counts match exactly.)
- **C-b pass**: 51 and 51, and the two lists are line-for-line the same constraints in the same order.
- **C-c pass**: every X-id restated with the same meaning by both.
- **C-d fail on count** (75, 68 ≫ 3). But the content is the opposite of the prose case. Nearly every item is an *absent constraint* — "ids are not required to be unique", "this field is not forbidden on other kinds", "no cross-file rule checks that this node exists", "nothing requires actual_exit to equal expected_exit on pass" — and the two readers report substantially the same set (≈85% overlap by inspection; both name the same top items). Readers of prose disagreed about what it *said*; readers of the schema agree about what it says and agree about what it leaves out. That is convergence on the artifact, with a shared to-do list attached.

**Real defects both readers found (fix now):**
1. `na_code` is in the row isolation enum but unreachable — every type conditional excludes it. Remove from rows.
2. An integration row of type `review` cannot pass: the integration conditional forces `red_evidence ∈ {checks_baseline, not_run}` while the type conditional forces `mutant`. Contradiction → `unresolved` forever. Scope the integration constraint to type `exec`.
3. `pass` does not require `actual_exit == expected_exit` (exec) or every section `pass` (excerpt). Validator rule.
4. No id uniqueness for nodes, checks, rules, issues, subagents, framing ids. Validator rule.
5. No existence check for `subject.node`/`subject.check`, `decisions.node`, `hypotheses.node`, `subagents.node`, `lessons.node`, `next_action.node`/`issue`, `evidence.from_node`. Validator rule.
6. `does[].produces` not required to be in `shape`. Validator rule.
7. `tier_rule` fired lines not checked against the node (review_only_check vs the node's checks; reads_three_or_more_upstream vs `len(upstream)`; needs_two_or_more_domains vs `len(needs)`). Validator rule.
8. X17 undefined at rows = 0. Define: rows = 0 → verdict `pass`.
9. Fields not forbidden on the wrong kind (split_reason, subject, guarded_by, open_issue). Schema `then: properties: {x: false}`.
10. `base`, `top`, "cause (d)" used in descriptions but undefined. Rewrite descriptions: base = index 0, top = last index, cause (d) = `under_capacity`.

**Fixes applied** (schema 51 → 66 conditionals, validator X01–X20 → X01–X26): all ten items. Example still validates; mutation suite 17/17 including one mutation per fix; node-id uniqueness now fires as X22 before any derived rule. README updated.

### T-19 rerun on the fixed schema + validator (one reader, broader brief incl. validate.py)

- **Schema conditional contradictions: 0.** The integration/review contradiction is closed and no new one was introduced. This is the criterion that matters for "can every enumerated combination validate": it holds.
- **Two-readings ambiguities (category f): 11**, down from the prose's 75 and now specific: X16 all-attempts vs latest; X13 for rows without a node; X17 "every delivery"; X12 scope and word/substring; X02/X14 exact vs normalized; X01 per node vs per check; code.gate one-vs-any; assumptions namespace; rules.section empty.
- **Validator-vs-x-crossfile discrepancies: 13** — real bugs in enforcing stated rules: X07/X08 silently skipped without `--models` and the run still says OK; X11 picks the first pass row rather than the gate row and skips the sha check silently; X13 ignores acceptance/integration rows; X18 is conditional on a verdict; X23 resolves next_action fields only on the matching kind; all X rules skipped when any schema error exists (nothing passes wrongly, but findings are hidden).
- **Cross-rule contradictions: 2** — X16 with X10 (a node that ever had a dissent row can never be `accepted`), and schema-vs-X20 (a code node with only review checks validates but can never pass X20).
- **Absences (a–d), 64**: fields not forbidden on other kinds (15), references not resolved (12), uniqueness (13), consistency (24). These grow with the precision of the question and are an open-ended backlog, not a convergence failure.

**Stopping rule (decided now, to avoid the prose spiral in schema form):** fix every item in the first four lines — contradictions, two-readings, validator discrepancies — because each is either a bug in enforcing a stated rule or a rule with two meanings. Do not chase (a–d) exhaustively; close only those the prompt's behavior depends on, and keep the rest as a counted backlog in the README. A validator that enforces its stated rules exactly, with no contradictions and no two-readings, is the target; "checks every conceivable consistency" is not.

### T-20 — schema-generated fixtures

`gen_fixtures.py`: walks the example record, generates delete / wrong-type / out-of-set / duplicate mutants for every leaf, derives from the schema whether each should be caught, runs validate.py. **594 mutants, 589 expected caught, 588 caught, 1 gap, 0 over-strict.** The gap: duplicate ids in `progress.assumptions` (X22 omits that list — the reader's item c-9). The five expected survivors are deletions of optional fields. First run took 90 s because `effective_required` rebuilt a jsonschema validator per leaf per conditional; cached.

What T-20 measures and what it does not: it measures that the validator enforces what the schema states (one-to-one with the schema's own constraints); it does not measure the absences the reader lists, because a generator derived from the schema cannot know what the schema omits. The two instruments are complementary: gen_fixtures for regression on stated constraints, a cold reader for absences.

The old comparison (v2.6 vs v1 markdown validators) does not transfer to the YAML format; those numbers stand as measured on the markdown fixtures and are not re-run.

**Fixed:** all 13 validator discrepancies (X07/X08 now require the ladder and say so; X11 uses the gate row and treats a missing artifact as a finding; X12 whole-word, six files; X13 covers acceptance/integration via subject key; X18 unconditional; X23 resolves whenever present; a NOTE line says when cross-file rules were not evaluated); both contradictions (X16 uses latest attempt per subject; a code node must have an exec check — schema conditional 67); the X22 gap (progress.assumptions); the 11 two-readings as x-crossfile wording (X01 per check, X02/X14 exact strings, X17 rows==0, …) and two descriptions. **gen_fixtures: 594/594, 0 gaps, 0 over-strict.** Backlog (a–e, ~64 items) recorded in the README with the stopping rule.

### State at close of 2026-11-03
- Prompt: v2.8, 2,780 words, behavior only.
- Record: schema (67 conditionals) + validator (X01–X27) + generator; example validates; 594 generated and 39 hand-written mutants all caught.
- Convergence: two cold readers agree on every field, conditional, and cross-file rule; 0 schema contradictions; 0 two-readings after fixes; absences are a counted backlog.
- Not yet done: a v2.8 run on a task that is not its own tooling (T-18's prerequisite); the markdown→YAML migration of the run-1/run-2 records is one example only.

**Finding F-17.** A schema converges on content in one round (0 differences in fields, conditionals, cross-file) where prose diverged (19 → 75 two-readings conflicts). The schema's open items are absences, which are closed by adding constraints and do not spawn new readings. The pre-registered C-d threshold (≤ 3) was the wrong criterion for a schema; the right one is "both readers report the same absences", which held.

## Run 4 — v2.8 on a task that is not its own tooling

Task: framing-lint, a stdlib linter for Part 3 of the Prompt Authoring Guide (RFC 6901 was first choice; both hosts off the allowlist; the guide text was already on disk). Lead: fable, depth 0. Delivered **complete**: 3 nodes, 0 retries, 7 of 20 node runs, 1 unchecked rule by stated assumption.

### Run findings
| id | finding | prompt implication |
|---|---|---|
| RF-1 | X18-unconditional contradicted the approval precondition (reviewer cannot exist before review). Caught by validate.py at the checkpoint. | validator fix; X18 now conditional on the review having run |
| RF-2 | three YAML flow-mapping parse failures writing the record by hand; prose with commas | lead-facing note: block style for prose fields; or the lead writes the record via a small helper, not by hand |
| RF-3 | the lead's assumption a3 contradicted the lead's own no-false-positive gate test; the haiku builder resolved toward the test and the spec; the assumption was wrong | v2.8 does not require framing assumptions to be checked against gate tests before dispatch; cheap to add as a lead step |
| RF-4 | integration.sh, lead-written run machinery, shipped a bug to the first integration run (pass+fail on every line; exit codes correct). No gate test existed although v2.8 says run machinery is a code output under test-first | the obligation exists and the lead skipped it; the deliverable-vs-machinery distinction (F-03) created a path the lead did not treat as gated. Template integration.sh, tested once, is the fix |
| RF-5 | the evidence auditor had to run integration.sh to reproduce its row, and integration.sh overwrites integration.out — the audit modified the record it audited. Surfaced by the auditor's `notes:` | the `notes:` channel (D30) paid for itself on its first real run. Fix: integration script takes an output path; auditor redirects |
| RF-6 | the lead under-filled `exercises:` on c1 at design time (1 id vs 35 actually exercised); the delivery `unchecked` computation showed 29/36 and exposed it | D28's unchecked list works as a detector of the lead's own bookkeeping; the correction was a record fix, not a verdict change |

### T-18 — obligation inventory (fired / did not fire on this run)

Fired, with effect: authority rule (no conflict arose, but rules.yaml derivation was performed under it); rules.yaml derivation (36 rules; produced RF-6); framing with unknowns→assumed and risks→guarded_by (produced RF-3 via a3); test-first with lead-written gate tests (69 cases; caught the a3 error through the builder); stub-to-red; per-gate green-at-baseline; tier rule (haiku, haiku, sonnet — all first-attempt passes); builder brief with Sequestered/may-not/stop rule; review gate with mutant, random A/B, verbatim anchor (first-try discrimination); carried-hash rule for c4; validate.py at approval and at delivery (caught RF-1, RF-2); evidence audit with `notes:` (produced RF-5); unchecked-rules computation (produced RF-6); hypotheses section (empty, no retries); lessons entries.

Did not fire (no occasion): correction edge and all five causes; dissent; escalated; void review; cause (e) source defect; degraded isolation; cost-pressure line; `{{PRIORITIES}}` tiebreak at integration (no conflict); irreversible-step rule; recoverable-copy-before-merge (no existing file merged); resumption override; threshold promotion.

Did not fire although the occasion existed: gate test for run machinery (RF-4) — the obligation was present and skipped.

Cut candidates from this run alone: none safely. Every obligation that did not fire is a failure path, and a run with zero retries exercises no failure paths. T-18 needs a run with at least one gate failure before it can name cuts; the prior calibration runs (which had failures) ran under earlier versions. **T-21**: run v2.8 on a task with a known-hard node (expect a correction-edge pass) and repeat the inventory. → Run 5 (done: two correction-edge passes; see the Run 5 entry below).

### Deliverable note
framing-lint works on the spec's own worked examples and 69 gate cases. It has not been run on a real RCA document; that is the obvious next use and would surface the false-positive rate on real prose, which the gate tests only sample (4 sentences).

### Protocol notes
- P-06: the second derivation cost 125k tokens and 6 minutes and disconfirmed a hypothesis that two more prose versions would have been built on. Run the convergence test before each version, not after.

### Protocol notes
- P-05: an independent spec-to-checklist derivation is cheap (one opus call, ~137k tokens) and found more than three runs of execution did. It belongs before any fixture is written, not after.
- P-04: file mtimes leak setup actions to a fresh designer. Restoring the plant at 21:45 was visible as a modification time. Future plants: touch all fixture files to a common mtime after setup.

- P-01: the planter (sonnet, sealed) and the g2 builder (haiku) independently converged on the same line. The builder's self-report disclosed the defect to the lead before delivery; the seal held only until a builder read the fixture. For future plants, the sealed defect should be one a builder would not naturally report in five lines, or the self-report should be withheld from the lead until after the gate verdict.
- P-03 (approved 2026-11-01 19:11): run-2 protocol. v1 lead factored into design(prompt, I) and triage(prompt, failure), both in one fresh opus subagent with state ∅ w.r.t. run 1; the depth-0 process only dispatches builders per the designer's briefs, runs the checks it names, and relays gate failures back to the designer for correction briefs. Confound recorded: run 1 lead was fable at depth 0, run 2 lead is opus at depth 1; no conclusion may depend on lead model identity.
- P-02: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` in this environment. Only the depth-0 agent can spawn builders. A v1 comparison run therefore cannot have a fresh subagent as lead; see the run 2 protocol (P-03) above.

## Run 5 — v2.8 (results only)

Reduced to results only; the run's task text is not published.

- Date: 2026-11-03. Prompt v2.8 (schema v2 at delivery). Lead: fable, depth 0.
- Nodes: 9. Node runs: 28 of 40 used. Delivery: complete.
- Verdicts: acceptance checks C1–C7 pass (7 of 7). Evidence audit: 0 miscited, 8 partial. Record validates (exit 0). Open issues carried at delivery: 6.
- Pre-registered tests: T-21 (correction edge with causes (b) and (c); hypotheses recorded before each retry, and the record held them) — **pass**.
- T-18 second check: no failure-path obligation was cut; the per-node framing line informed nothing and was replaced (see RF-8).
- Decisions taken after this run (in "Schema v2 + v2.9"): D34 tier lines frozen at dispatch; D35 phase attribution; D36 exec availability per check with a residue path, per-node framing line removed; D37 a reviewer brief adds no property; D38 fan-in line kept, pre-registered as T-22.

| id | finding | what it means for the kit |
|---|---|---|
| RF-7 | the validator rejected three tiers set by feel; the computed tiers stood | the tier rule works as a check on the lead; fan-in alone raises a node's tier even when it copies, so fan-in should count only when the node reconciles its inputs (T-22) |
| RF-8 | a check reclassified after dispatch left the record unable to show the tier the builder ran at | freeze the tier at dispatch in the record (D34); ask whether exec is available per check, not per node (D36) |
| RF-9 | integration-phase reviewers and decisions had no node to attach to | allow phase attribution where no node applies (D35) |
| RF-10 | an exec check over prose returned hits on the merged output, none a real miss | an exec check over prose declares its residue path at design time, and its review half needs a mutant (D36) |
| RF-11 | the correction edge fired twice in one chain; the second failure came from a reviewer brief stricter than its check | a brief is a second place a check can go wrong; a brief adds no property to the check (D37) |
| RF-12 | the evidence audit's notes channel carried the one finding that could change the design; the row verdict would not have | keep audit notes mandatory |

## Schema v2 + v2.9 (2026-11-03, after run 5)

Decisions (the full text was in that version's background document, which is not published): D-S records v2.8's format-by-reference change, which had no background file (the v2.8 prompt cited a background file that was never written — a finding in itself: the background ledger lapsed for one version). D34 tier lines frozen at dispatch (RF-8). D35 phase attribution (RF-9). D36 `exec_available` per check with residue path, `program_considered` removed, X28 (RF-8, RF-10). D37 reviewer brief adds no property (RF-11). D38 fan-in line kept, pre-registered as T-22 (RF-7).

Verification: validate.py on the migrated run-5 record exits 0; example record exits 0; 15 targeted tests for the new rules pass (`test_v2_rules.py`, shipped at `plugins/graph-prompt/skills/graph-record/scripts/test_v2_rules.py`, written against the rules before the migration of the run-5 record); gen_fixtures on the example: 594/589/589, 0 gaps. gen_fixtures on a large record (second fixture base, exercising phase and the X25 exemption) was stopped at the 30-minute limit: each mutant spawns validate.py as a subprocess (~1 s). Tooling note: gen_fixtures should validate in-process. Not re-run; `test_v2_rules.py` covers the v2 values the example lacks.

Prompt: v2.9 is 2,901 words (+121 over v2.8). Two behavior lines added (D36, D37); nothing cut from the prompt, because the cut candidate (`program_considered`) lived in the schema. D13 stays disconfirmed for a fourth version. The first prompt-text cut still has no evidence base: run 4's T-18 inventory found the never-fired obligations all failure paths with no occasion, run 5 cut none of them (its results entry records no cut), and cutting an untested path is not a cut, it is a bet.

### Future tests (added)
| id | test | question | needs |
|---|---|---|---|
| T-22 | On the next two runs, for each node where `reads_three_or_more_upstream` fires alone, record whether the content reconciles inputs or copies them | does fan-in raise difficulty, or only token count? | two runs |
| T-23 | Plant a source conflict in run 6 (two {{SOURCES}} files disagreeing on a fact the deliverable must use) and, separately, a check whose mutant a weak reviewer would miss | exercise the authority halt, cause (e), void review, and dissent, which the five runs so far (1–5) have never reached; the only route to a T-18 cut | run 6 design; P-04 mtime hygiene |
| T-24 | Cold-read v2.9's two new lines (D36, D37) with one reader deriving the rule list, compare to the author's | P-06: convergence before the version is used, not after | one opus call |

### T-24 result — rule list converged on the third read; ambiguity count did not
Three cold reads (opus, fresh context each) of the three changed passages, the prompt rewritten between reads 1→2 and 2→3, with the `partial` residue definitions moved from prose into the schema before read 3 (read 3 was also allowed the schema's `check` definition and X28).

| read | P1 rules / ambiguities | P2 | P3 | rule list vs intent |
|---|---|---|---|---|
| 1 | 7 / 11 | 4 / 7 | 2 / 6 | P1 missed the layer_5 A/B protocol; P2 read "the brief" as possibly the builder's; "structural" collided with the merge sense |
| 2 | 10 / 10 | 5 / 8 | 3 / 6 | P1 matched; P2 unclear whether a void or a cause-(c) attempt; "partial" collided with "partial run" |
| 3 | 15 / 9 | 8 / 8 | 5 / 6 | all three matched the author's intent line for line |

Reading: the derived rule list is the convergence criterion (as T-19 found for the schema); the ambiguity count is flat across rewrites (24, 24, 23) and is a property of prose, not of a draft. The ambiguities that would change a lead's action were settled as rulings R20–R28 (the published rulings file, `plugins/graph-prompt/skills/graph/references/graph-prompt-rulings.md`, holds the v2.9 section) and one schema constraint (`partial` ⇒ `exec`). Cost: 3 × ~85k tokens.

Post-pass fix (2026-11-03 16:15): the schema still required `node.unavailable` only on review-only nodes, which D36 made wrong — a node with one exec and one `no` check had no place to record what was tried. Now required per `no` check, `reviewer_tier` per review check; run-5 nodes migrated; test added (16 tests). Also: the rulings file was renamed (it had carried v2.7 in its name through three versions).

Finding F-18: moving a definition from prose to the schema cut the P1 rule list's misreadings to zero in one step (read 2 → 3) where two prose rewrites had not; the prompt should carry the obligation and the schema the object, every time — D-S applied at the sentence level.


## Run 6 — T-23 pre-registration (2026-11-03 16:20, written before the plant)

Purpose: give the never-fired failure paths an occasion. The five runs so far (1–5) have not reached the authority blocker, cause (e), void review, or dissent. Two are planted; two are observed.

Task (small, deterministic, three nodes): a changelog report generator. {{SOURCES}}: `spec.md` (CSV columns, invariants, report format) and `events.csv` (about 60 rows). Nodes: parse (code, deterministic, gate test lead-written), report (code, rule-encoded: template rendering, exec + review), index/README (judgment, review). {{CHECKS}} C1–C4 as drafted by the lead; {{LIMIT}} 20 node runs; interactive mode; lead fable depth 0; prompt v2.9, schema v2.

Plants (a sonnet planter writes both source files and a sealed record (not published); the lead reads the sealed file only at delivery; all source files touched to one mtime after setup, P-04):
- Plant A — cause (e) at a gate. `events.csv` violates one invariant that `spec.md` states, at a location a builder's five-line self-report would not naturally mention (P-01), such that a correct parser passes its own tests and the lead's gate test on the output fails. Expected path: gate fail → hypothesis cause (e), no retry → open issue `source_defect` naming file, line, rule, two unblock options → interactive ask → person decides → continue.
- Plant B — authority blocker at design. One {{CHECKS}} item the lead drafts will contradict `spec.md` on a rendering rule. This plant is in the lead's own inputs, so it is not sealed: the lead writes C4 to contradict the spec knowingly, then must behave as the rule says when designing (report the conflict as a blocker before approval, write no check that accommodates it, ask). Confound: the lead knows. What is tested is whether the obligation is followed when the lead has every reason to skip it, not whether the lead notices.

Observed, not planted: void review (expected to have an occasion only if the tier rule puts a haiku reviewer on a subtle mutant); dissent (needs a builder to return `cannot address` twice on a check the lead upholds; cannot be planted without scripting the builder, which would test nothing).

Pass criteria, fixed now:
| occasion | pass |
|---|---|
| authority blocker | an open issue of kind `blocker` naming C4 and the spec line exists before the approval pause; C4 is not rewritten before the person answers; the person is asked |
| cause (e) | the parse node's gate row is `fail` with a hypothesis entry of cause `source_defect`; no attempt 2 before the person answers; the open issue names file, line, invariant, two options; the sealed file's location matches the open issue's |
| void review | if it occurs: recorded as void, counted against LIMIT, not an attempt; the second review has a replaced brief or tightened check |
| dissent | if it occurs: both positions recorded; delivery states partial |
| T-18 third inventory | every obligation listed fired / did not fire; cut candidates named only from paths that have now fired at least once |
| T-22 | for any node where `reads_three_or_more_upstream` fires alone, record reconcile vs copy |

Disconfirmation of the run's value: if both plants fire exactly as the prompt describes on the first occasion, the paths work and T-18 may cut nothing on their account; if either path is skipped or mis-recorded by the lead, that is the finding.

### Run 6 result (2026-11-03 16:50; sealed file opened at delivery)

Delivered **complete**: 4 nodes (parse, report, generate, readme), 6 of 20 node runs, C1–C4 pass, evidence audit 10 of 28 sampled / 0 miscited, record validates. Both plants fired and both paths ran as the prompt describes.

| occasion | result | pass criterion met |
|---|---|---|
| authority blocker (plant B) | rules.yaml derivation surfaced c4 ⟂ s-r3; open issue oi1 `blocker` with `tried` written before approval; c4 untouched until the person answered; AskUserQuestion at the approval pause. Person: "What's the standard used in the rest, the schema and prompt? Make them consistent." → c4 restated to R3 as an exec check, recorded as the person's decision | yes |
| cause (e) (plant A) | parse builder (haiku) hit the data-validity test, invoked the stop rule and reported row 50 / I1; the lead ran the gate (1 failed / 18 passed), verified the duplicate independently (`uniq -d` → 38), recorded hypothesis `source_defect` with its disconfirmation, open issue oi2 with file/line/rule/unblock, no retry, asked. Person: "Explain. I want to fix the bug and have valid test results." → explained that the bug is in the data; corrected line 51 (id 38→50) as the person's edit, `sources_changed` decision with before/after hashes, attempt 2 = same artifact re-gated, 19/19 | yes |
| sealed check | the sealed record (not published): I1, data row 50, line 51, original row `50,2026-09-30,…` — matches oi2 exactly; the correction applied (id 50) equals the planter's unplanted row | yes |
| void review | no occasion: the one review (readme, sonnet reviewer) discriminated its mutant first try | — |
| dissent | no occasion | — |
| T-22 | no node fired `reads_three_or_more_upstream` (readme reads 2) | no data |

### Run findings
| id | finding | prompt implication |
|---|---|---|
| RF-13 | an unknown whose disposition is `asked` must carry an `answer`, but at the approval pause the question is open; the record held `answer: pending…` as a workaround | schema: add disposition `pending` (asked, not yet answered), legal only while next_action is `blocked` |
| RF-14 | the stop rule made the seal moot: the haiku builder's self-report named the row and invariant before the gate ran (P-01 again). This is correct behavior — the stop rule exists for exactly this — and the gate verdict was still computed by the lead from the test run, not from the report | no change; note for planting: a builder with a stop rule will always disclose a source defect it detects, so the seal only tests whether the lead verifies independently (it did: `uniq -d`) |
| RF-15 | the lead's gate test encoded framing assumption a1 (data valid) as `test_sources_events_csv_is_valid`. This is what made cause (e) detectable at the gate rather than at `generate`; it is also RF-3's pattern (an assumption inside a gate test) used on purpose | v2.9 candidate line: every framing assumption that a gate test depends on is named in that test's docstring, so a cause-(e) fail is traceable to the assumption it falsifies |
| RF-16 | the schema already required `file`, `line`, `rule`, `unblock` on a `source_defect` issue — the validator rejected the first draft of oi2 that lacked them. The prompt's cause-(e) sentence and the schema agree; the lead had to be told twice | evidence that format-by-reference works at the failure path, not only the happy path |
| RF-17 | `generate` as a `kind: code` node (deterministic step, program not subagent) had no stub-to-red of its own; its red evidence is the parse attempt-1 run on the uncorrected data, recorded as `checks_baseline` | fine for a step whose program is the upstream deliverable; a rule is missing for what red means for a `code` node that runs an upstream artifact. Candidate: "a code node's red is the gate of the node that produced its program" |

### T-18 — third inventory
Fired for the first time: authority rule as a blocker (oi1); cause (e) with no retry and the interactive ask; `sources_changed` decision; `source_defect` open-issue fields; the approval-pause AskUserQuestion carrying a blocker; a `kind: code` node; `inspect` gate with `minimal_inspect` red evidence; `phase: audit` and `phase: integration` attribution (schema v2); `exec_available` on every check; `node.unavailable` on a mixed node (report: exec + inspect).

Fired as before: rules.yaml derivation (34 rules; it is what surfaced the c4 conflict), test-first with lead-written gate tests (27 cases) and run-machinery tests (11), stub-to-red at assertion level (the lead fixed two stubs that crashed instead of asserting — layer_5's borderline rule applied twice), tier rule (haiku, haiku, —, sonnet), builder briefs with stop rule (fired once, correctly), review with mutant and random A/B (1 of 1 discriminated), carried nothing (no hash-equal integration items this run), validate.py at approval and delivery, evidence audit with `notes:` (produced oi3), lessons entries.

Still never fired, six runs: dissent; escalated; void review; cause (d) under-capacity; degraded isolation; cost-pressure line; `{{PRIORITIES}}` tiebreak at integration; irreversible-step rule; resumption override; threshold promotion.

Cut decision after three T-18 checks (runs 4–6): the authority rule and cause (e) have now fired and worked, so they stay on evidence, not on faith. Of the still-unfired ten, three are cheap terminals the schema's verdict table needs (dissent, escalated, void); three guard conditions a different environment would hit (degraded isolation, resumption, irreversible step); the remaining four — cause (d), cost pressure, the priorities tiebreak, threshold promotion — have had no occasion in six runs and ~170 words between them. **Proposed cut for v3.0: cause (d) folds into (a) with the tier move as a lead option (the schema's `escalations` field stays); the cost-pressure line and the priorities-tiebreak sentence go; threshold promotion stays in the learning edge (it is the lessons mechanism, not a run path).** Pre-registered as T-25: v3.0 with those cuts, two runs, no finding attributable to a cut line.

## Schema D39 + v3.0 (2026-11-03 17:45)

- D39 (RF-13): `unknowns[].disposition` gains `pending` + `issue`; X29 ties it to a live blocker. 19 targeted tests pass; all three records validate.
- D40: the first cut. v3.0 = v2.9 minus cause (d) as a separate branch (folded into (a) with a mechanical trigger: second builder error on a node → one tier up), minus the cost-pressure line, minus the integration tiebreak (check-vs-check conflict joins the authority rule as a blocker), minus the threshold-promotion clause; plus one sentence defining blocker handling once (interactive asks; autonomous blocks the affected set and runs the rest), which the source-defect line now references instead of repeating. 2,933 (a later count) → 2,892 words (−41). Under D13's test this is the first cut of prompt text (v2.8's shrink, L341, came from moving the format out of the prompt, with every obligation retained).
- T-24 method reused (two cold reads): the first read found the folded cause (a) *worse* than the branch it replaced (the escalation trigger "wrong in a way the brief covered" is always true, so the choice of tier was undetermined) and found that no line said who resolves a check-vs-check conflict. Both fixed before use: the trigger is now a count (second (a) → up), and blocker handling is stated once. Second read: rule lists match intent; residual readings settled as rulings R29–R35.
- F-19: a cut can create an ambiguity where there was none. Folding (d) into (a) reused (d)'s own trigger phrase, which had been tolerable as a *label* for a branch and became ambiguous as a *condition* for a tier choice. The fix (a count) is better than either version. Cuts need the same cold read as additions.
- T-25 stands as pre-registered: two runs on v3.0; pass if no finding traces to a cut line.

## Run 7 — v3.0 (results only)

Reduced to results only; the run's task text is not published.

- Date: 2026-11-03 (setup 18:30, delivered 19:50). Prompt v3.0. Nodes: 8. Node runs: 27 of 40 used. Delivery: complete.
- Verdicts: acceptance checks C1–C6 pass (6 of 6). Evidence audit: 1 miscited (3.7%), 7 partial. Record validates. Open issues carried: 4.
- Pre-registered tests: T-25 first run (no finding traces to a removed v3.0 line) — **pass**. T-22 — no node fired the fan-in line alone; no data.
- Decisions taken after this run (v3.1): D41 per-element verdicts on enumerable review sections; D42 token-fixable checks are exec or partial; D43 input facts bind the deliverable, and conflicts with them are blockers; D44 audit notes before counts; D45 three schema-redundant field lists cut. Rulings R36–R41.

| id | finding | what it means for the kit |
|---|---|---|
| RF-18 | an output did not parse; the review gate checked its semantics and passed it, though a parser was installed and never run; the first detection was the person's | a structural property with a program oracle goes to an exec check (D36) |
| RF-19 | two fresh reviewers of one unchanged table flagged different elements; the second found some the first missed | a review verdict is a sample; cap the attempts; a retry brief names the rule, not the cells (D41) |
| RF-20 | the lead ran a review fail without a mutant; the validator refused the verdict | the validator enforces failure-path obligations (the second case after RF-16) |
| RF-21 | a retry review keyed to an acceptance item had no admissible hypothesis key | the validator admits acceptance-item ids in hypotheses |
| RF-22 | the count-based escalation (a second builder error on a node moves it one tier up) fired and was followed without judgment; the first tier failed twice on citation hygiene and the next tier passed | the count rule works as rewritten; citation-heavy outputs may start one tier higher (lessons candidate) |
| RF-23 | a fail whose fix was a missing token cost four one-line returns and four re-reviews, with no change in meaning | if the fix is a token, the check is exec or partial, not review (D42) |
| RF-24 | an evidence audit found a premise cited to an input that did not say it | input facts bind the deliverable (D43); audit notes come before counts (D44) |

## v3.1 (2026-11-03 21:00, after run 7)

Changes: D41 per-element verdicts on enumerable review sections (RF-19); D42 token-fixable checks are exec/partial (RF-23); D43 input facts binding, in rules.yaml, bounded by "says no more than it says", conflicts with them blockers (RF-24, C4); D44 audit notes before counts (RF-24, RF-12); D45 three schema-redundant field lists cut (RF-16/20/21). 2,892 → 2,965 words (+73): four behavior additions, one cut.

T-24 method, one cold read (opus): all four rule lists matched intent on the first read; two passages reworded for action-changing readings (P1's antecedent and the blocker list; P3's consequence and how the element set is named); the rest settled as rulings R36–R41. The reader's own answer to "how would a lead decide 'says more than it says'" became R40 verbatim — the first time a cold reader supplied the ruling rather than the ambiguity.

Validator: X23 admits acceptance-item ids in hypotheses (RF-21). 19 schema tests pass; the three records (example, run 6, run 7) validate.

Open on the prompt side: T-25's second run (v3.0 cuts) is now folded into v3.1's first run — the cuts are unchanged in v3.1, so run 8 on v3.1 counts for both. T-26 (new): D41 and D42 together should cut correction cost; run 8's correction share of budget vs run 7's 44% is the measure, pass if under 25% with at least one correction occurring.

## Run 8 — v3.1 (results only)

Reduced to results only; the run's task text is not published.

- Date: setup 2026-11-03 22:30; delivered partial 2026-11-04 04:30. Prompt v3.1. Nodes: 9. Node runs: 50 of 50 used (limit reached). Delivery: partial.
- Verdicts: acceptance checks c2–c7 pass; c1 open (uncited citation forms in accepted artifacts, found by the residue review at the limit and listed as open token fixes). Evidence audit: 0 miscited, 1 not-found-sourced, 2 partial (2.7%). Record validates. Open issues for the person: 12. Mutants: 19 of 19 discriminated, none survived. First-attempt review pass: 5 of 14 gates (36%).
- Pre-registered tests:
  - T-25 second run (no finding traces to a v3.0 cut line): **pass**; the fold of cause (d) into (a) fired once and worked.
  - T-26 (correction share under 25%, with at least one correction): **fail**, 20 of 50 runs (40%) against 44% in run 7. Cost per correction fell; the count of corrections rose with the number of review gates.
  - T-22 (fan-in line): four observations for, zero against, across runs 7–8; the line stays.
- Mid-run: a ruling written into a reviewer brief was corrected (R43) and the review rerun (see RF-30).
- Decisions taken after this run (v3.2): D46 agreement-with-itself as a standing property of every review check; D47 gate programs sequestered from builders, and a brief's interpretations recorded as rulings before dispatch; D48 the reviewer receives the node's reads; D49 a reserve of the last tenth of the limit for one-item corrections and final runs; D50 tooling cold read before baseline, with filter edits listed. Rulings R42–R46.

| id | finding | what it means for the kit |
|---|---|---|
| RF-25 (×2) | a partial filter was passed by rewording the flagged sentences rather than fixing them; both builders reported the rewording | the residue hand-off includes each builder's list of changed sentences (D50) |
| RF-26 | builders read the gate code and shaped their output to its format | gate code is withheld from builders (D47) |
| RF-27 (×4) | review gates passed while the reviewer listed real defects outside their checks | internal consistency becomes a standing property of every review (D46) |
| RF-28 (×2) | a copied exec check kept the previous run's root path and reported the wrong counts; the lead caught it only because the count looked wrong | an exec check names its root or runs from a stated directory; carried tooling gets a cold read (D50) |
| RF-29 | a reviewer not given an in-set file failed a rationale that rested on it | the reviewer receives the files the node reads (D48) |
| RF-30 (×2) | a ruling written into a reviewer brief voided two fails | an interpretation the brief adds is a recorded ruling before dispatch; a fail resting on a conflicting ruling is void (D47) |
| RF-31 | retired phrasing in accepted artifacts surfaced only when a filter's patterns were widened by a builder's report | a partial filter gets a cold read ("what would this miss?") before the run (D50) |
| RF-32 | a lead reading a filter's output is not a gate; the schema refused the verdict | the schema's failure paths hold (third occurrence, after RF-16 and RF-20) |
| RF-33 | the run limit arrived with a known one-token defect and no path to fix it; the run delivered partial | a correction reserve at the end of the limit (D49) |
| RF-22 (again) | two runs, two escalations on citation-heavy nodes that started on the lower tier | citation-heavy output starts on the higher tier (lessons candidate) |

## v3.2 (2026-11-04 05:10, after run 8)

Changes: D46 agreement-with-itself as a standing property of every review check, counted as in `fails_when` and open to a mutant; observations on a pass triaged (revise-and-re-gate / open issue / nothing) as decisions (RF-27 ×4). D47 gate programs sequestered from builders for non-code outputs (run, not open); a brief's interpretation is a decision of kind `ruling` before dispatch, and a fail resting on a ruling that any already-accepted artifact contradicts is void and counts toward escalation (RF-26, RF-30 ×2). D48 the reviewer receives the node's `reads`, read for cited passages (RF-29). D49 the last tenth of {{LIMIT}} is a reserve for one-item corrections, their re-gates, integration and the audits; schema `usage.reserve_runs`, rule X30; interactive mode asks to raise the limit before partial (RF-33). D50 tooling cold read before baseline: `exec` commands name their root, carried programs read for the previous run's constants, a fresh subagent asked what each `partial` filter would miss; builders list filter-driven rewrites in `filter_edits:` for the residue reviewer (RF-28 ×2, RF-31, RF-25 ×2). Rulings R42–R46. Schema: `decision.kind` gains `ruling`; `usage.reserve_runs` + X30; 21 validator tests; the three records validate.

T-24 method, two cold reads (opus): the first found every one of the five passages ambiguous in at least one action-changing way and supplied four findings beyond them (F-20: audits could never be funded at exactly the limit — a defect since v2.6; F-21: the draft sent builder text to a reviewer one sentence after sequestering it; F-22: "never reads the gate" vs "may run the check"; F-23: "patterns are asked" named no one). The second read passed four of five and closed two gaps (the brief's "exactly" list; the scope of "an accepted artifact"). The reader's own rewrites were adopted twice. This is the first version whose every new line was read cold before use, and the first where a reader found a defect older than the version under test.

Size: 2,965 → 3,365 words (+400, two D45 cuts included). D13's shrink hypothesis stays disconfirmed: v3.2 is the second growing version since v3.0's cut (v3.1 +73 words, v3.2 +400); the additions trace to twelve findings, each with two or more occurrences or a decided run outcome.

Pre-registered for run 9 (replacing T-26): T-27 cost per correction ≤ 2.0 node runs; T-28 first-attempt review pass rate ≥ 60% at the node level; T-29 no check revision mid-run adds internal consistency (D46); T-30 no finding traces to a path, file list, or pattern carried from a previous run (D50); T-31 no void traced to an unrecorded brief interpretation (D47). T-22 continues (fan-in line: four for, zero against).

## Run 9 — v3.2 (results only)

Reduced to results only; the run's task text is not published.

- Date: 2026-11-04, 07:12–09:40 ET. Prompt v3.2. Nodes: 6. Node runs: 24 of 25 used (runs 23–24 in the reserve). Delivery: complete.
- Verdicts: acceptance checks c1–c6 pass (6 of 6). Evidence audit: 0 miscited, 0 not-found-sourced, 2 partial. Record validates (schema and X01–X30). Mutants: 9 of 9 caught. First-attempt reviewer pass: 4 of 5 node gates. Open issues: 5.
- Pre-registered tests:
  - T-27 (cost per correction ≤ 2.0): **pass**, 2.0.
  - T-28 (first-attempt reviewer pass ≥ 60%): **pass**, 80%.
  - T-29 (no mid-run check revision adds internal consistency): **fail**; two did (RF-35).
  - T-30 (no finding traces to carried tooling): **pass**.
  - T-31 (no void from an unrecorded brief interpretation): **pass**; zero voids.
  - T-22 (fan-in line): five observations for, zero against.
- Decisions taken after this run (v3.3): D51 a quotable contradiction is a fail, never borderline; D52 filter_edits covers every changed sentence, whatever the reason; D53 a copied value is declared as a read, or mutual copies are merged.

| id | finding | what it means for the kit |
|---|---|---|
| RF-34 | the builder returned `filter_edits: none` while its self-report described rewording that a filter had flagged; the field existed but the brief did not define it | define the field in the brief: every sentence changed after a check listed it, whatever the reason (D52) |
| RF-35 | the standing self-agreement property was applied unevenly; a reviewer twice called a quotable contradiction "borderline" and passed it | a quotable contradiction is a fail, and the return has no third value (D51) |
| RF-36 | a node copied a value from another node's file and was gated before that node changed the value; the stale copy was caught only by reading a self-report | a node that copies another node's counts declares that node in its reads, so it is gated after; or the count is substituted at build time (D53) |
| RF-37 | the pre-run question "what would this filter miss?" found a class with zero coverage, shorthand forms, and a negation hole | the cheapest step paid for itself; keep it (D50) |
| RF-38 | the reserve carried the integration and audit runs past the ordinary limit, as designed | evidence for the reserve (D49) |

## v3.3 (2026-11-04 09:10, after run 9) [time as recorded at the time; run 9 is dated 07:12–09:40 ET at L629, and this log does not settle which is right]

Changes: D51 a quotable contradiction of the standing kind (count, list, label, cross-reference) is a fail, never a borderline; the return has no third value; a wrong upstream value is cause (b) (RF-35). D52 `filter_edits:` defined as every sentence changed after a check listed it, cumulative, the builder's own runs included; `none` is a claim the self-report must not contradict, rebuilt by the lead under a decision; retry edits belong to the one `changed:` item (RF-34). D53 a spec that copies a value from another node's output names that node in `reads`; mutual copies merge or read a third node; a copy found after approval gets its edge and a re-gate (RF-36, promoted lesson from runs 8–9). One cold read (opus); every passage rewritten once on it. 3,365 → 3,501 words. Schema unchanged.

Pre-registered for run 10: T-32 no check revision adds an internal-consistency property (D51; T-29 restated); T-33 no builder's self-report describes a rewording its `filter_edits:` omits (D52); T-34 no stale copy found by a reader (D53); T-27/T-28 continue (cost per correction ≤ 2.0; first-attempt reviewer pass ≥ 60%); T-22 continues.

## v3.4 (2026-11-04, after an external review of the v3.3 kit)

Input: a Codex-side review of the v3.3 kit (bug report with 13 numbered validator defects and failing tests [the table below accounts for 12 of the 13; BUG-10's disposition is not recorded in this log]; a compatibility report; three patches — validator fixes, opaque subagent ids, an optional Codex skill with an adapter and release-import scripts). Assessed by running the patched validator against the real records (the example and the earlier runs' records) before accepting anything.

| item | disposition | why |
|---|---|---|
| BUG-01, 04–09, 11–13 (duplicate YAML keys; X06 roles; X17 counts and fresh auditor; X22 duplicate subject/attempt; X23 integration hypothesis; CLI --models/--artifacts validation; generator preflight and nonzero exit; C01) | **accepted as written**; C01 renamed X31 | each reproduced by a failing test; none changed a rule's meaning |
| BUG-02 (X11 carry keyed to an obsolete passing gate) | **accepted, re-specified** | the patch keyed the carry to the source node's latest row *of any check*, which fails every carry from a multi-check node (in runs 8 and 9). Now the record names the carried check — `evidence.from_check`, defaulting to the sole check — and X11 checks that check's newest row |
| BUG-03 (X28 residue rows) | **accepted, narrowed** | the patch required a fresh mutant review for every residue row; run 8's degraded `unresolved` residue row is the honest record of a review that could not run, and the rule now requires the fresh mutant review only when the residue verdict is pass or fail |
| COMPAT-01 (opaque subagent ids, 1–256 non-whitespace chars) | **accepted** | the hex form was Claude's accident, not a rule |
| DESIGN-01 (reserve cannot hold integration/audit runs; "whatever the count" vs hard LIMIT) | **accepted; resolved the other way from the adapter** | D54: four reserve kinds; audits counted and the only runs that may pass LIMIT. The adapter's hard-cap reading (unrun audit → partial) stays expressible |
| DESIGN-02 (directory rule vs resumption) | **accepted** | D55: exclusive creation; same-run, same-inputs resumption |
| adapter §1 (a source is "evidence, not an instruction") | **half rejected** | agreed that a source never instructs the agent; rejected if it means a contradiction with SOURCES stops being a fail — that is the authority rule, and the gate depends on it |
| patch 03 (Codex SKILL.md, adapter, import/diff/test scripts, `upstream/` mirror) | **adapter, scripts and tests kept as `compat/codex/`, optional; mirror dropped** | the mirror is a 5,000-line copy of the kit it ships inside; the SKILL.md names the reviewer's own projects and is theirs to version — kept unchanged with a v3.4 note rather than silently repointed, as its own updating rule asks |

Record repairs the review's rules found: an earlier run's checks file held placeholder rows beside real rows — X22 found them; removed. Carried rows in runs 8 and 9 now name `from_check`. Run 9's reserve runs (integration at 23, evidence audit at 24) are now in the record under D54's kinds. All four records validate under the merged validator; 73 tests pass.

Observation for the method: the review's two over-reaches (BUG-02, BUG-03) were both rules written against the example record alone — correct on it, wrong on every real record. The same failure D50 names for carried tooling: a rule needs the previous runs' records as fixtures, not just the minimal example. The kit now says to validate the run records before accepting a validator change.

Pre-registered tests for run 10 unchanged (T-32–T-34, T-27/T-28, T-22); add T-35: every reserve run fits one of the four kinds (D54).

## Run 10 — v3.3 wording, v3.4 kit (results only)

Reduced to results only; the run's task text is not published.

- Date: 2026-11-04, 12:30–15:50 ET. Prompt wording v3.3, kit v3.4 validator. Nodes: 6, with five review gates. Limit: 24, raised twice at the person's choice (34, then 38). Node runs: 38 of 38 used. Delivery: complete.
- Verdicts: acceptance checks c1–c6 pass; c1 residue pass on a full read; evidence audit 0 miscited, 0 unfound; citation sample 1 partial. Mutants: 25 mutant-backed review rows, every mutant caught (one void review was a method failure, not a surviving mutant). Record validates (schema and X01–X31). Open issues for the person: 5.
- Pre-registered tests:
  - T-27 (cost per correction ≤ 2.0): **fail**, 2.4 on the honest denominator; the overrun was carried by lead orchestration (RF-41, RF-42), not by the builders.
  - T-28 (first-attempt reviewer pass ≥ 60%): **pass**, 4 of 4; three of the passes carried an observation that was a defect (RF-39).
  - T-32 (no check revision adds an internal-consistency property): **fail**; two revisions did (RF-39).
  - T-33 (no self-report describes a rewording its filter_edits omits): **pass**; the cumulative field cannot be kept across fresh contexts (RF-40).
  - T-34 (no stale copy found by a reader): **fail**; one stale copy was found by a reader, inside one file (RF-39).
  - T-35 (every reserve run fits one of the four kinds): **pass with a representation gap** (RF-44).
  - T-22 (fan-in line): six observations for, zero against.
- Decisions taken after this run (v3.4 and v3.5): D54 four reserve kinds, with audits counted and the only runs allowed to pass the limit; D55 exclusive creation of a run directory, with same-run resumption only; D56 the standing self-agreement property reaches the whole artifact; D57 filter_edits per attempt, with the lead carrying earlier lists into retry briefs; D58 a hunk-trace rule admits sentences returned by a later gate; D59 re-gates follow the dependency order; D60 residue reviews over a set read every file and return a ledger; D61 unchecked rules are recorded before approval (X32). R47 is cited with the reserve re-base (RF-44).

| id | finding | what it means for the kit |
|---|---|---|
| RF-39 | reviewers applied the self-agreement property to the sets a check enumerates, not to the whole artifact; three gates carried quotable contradictions as observations | the verdict rule covers every count, list, label and cross-reference in the artifact; an observation that quotes a contradiction is a fail (D56) |
| RF-40 | a fresh-context retry builder could not keep a cumulative filter-edit list; the lead merged every time | the lead hands earlier attempts' lists into the retry brief and merges them (D57) |
| RF-41 | a hunk-trace rule predated corrections that the integration gate ordered on the same file; two re-gates failed on it | a hunk-trace rule admits, by construction, sentences returned by a later gate (D58) |
| RF-42 | a fan-in node was re-gated in parallel with its upstreams' re-gates and failed on their changes | a node is re-gated only after every upstream it reads is accepted at its newest attempt (D59) |
| RF-43 | a residue reviewer over a file set diffed the two sets and grepped instead of reading; the rerun, told that diff or grep verdicts are void, read every file and found shared over-claims | a residue review over a set reads every file and returns a per-file ledger (D60) |
| RF-44 | the reserve list held one reserve; two raises re-based it twice, and earlier reserve runs became ordinary | the reserve record carries a limit per entry or the superseded list (D54 note) |
| RF-45 | the residue read's finds were pre-existing sentences in changed files; each fix needed its owner's return and re-gate, eight runs in all | consider a citation-scope review at each node gate for every file the node writes |
| RF-46 | the first escalation of the calibration (to opus, at the second cause (a)); the opus reviewer found nothing the revised check had not already named | no evidence that the tier mattered; the check revision did |

## v3.4 second external review (Codex handoff 2, 2026-11-04 17:20) → kit v3.4.1

Input: a second Codex-side review of the v3.4 kit (bug report V34-01…05 and KR1–KR4, a compatibility report, a trial of the kit on the reviewer's own architecture task with findings TRIAL-01…13, three patches). Assessed as before: the core patch applied to the current kit, every real record revalidated.

| item | disposition | why |
|---|---|---|
| V34-04 X27 enforced (progress.assumptions ids must exist in framing.assumptions) | **accepted** | a documented backlog item, closed with their 3 regressions; every record holds |
| V34-05 X12 conflicts with a quoted source sentence containing "Proven" | **accepted** | real: the authority rule requires exact quotes in rules[*].quote and X12 banned the word everywhere; the exception is scoped to that one field's literal scalar, with authored text, comments, anchors and aliases still screened (12 regressions). Prompt sentence narrowed. Their implementation is heavier than needed (YAML token masking) but contained and tested; ported as is |
| BUG-02 follow-on: carry regressions (test_carried_check.py, 8 cases) | **accepted** | they exercise the from_check selection as re-specified in v3.4 |
| V34-01 pre-dispatch readiness companion (preflight.py: prepare → independent coverage review → seal → verify) | **Codex-side; the kit-native half becomes a v3.5 item** | the finding is right: the validator accepts a record with no rule→check mapping and no final acceptance definitions, and the prompt promises both ("give every CHECKS item a row naming the rules it exercises or none; list every rule with no exercising check as unchecked"). A run's record could exercise its given-rules only implicitly. v3.5: `progress.unchecked_rules` + X32 (every rule id in some `exercises` or in `unchecked_rules` before approval). Sealing and fingerprinting stay in the adapter |
| V34-02, V34-03, KR1–KR4 (importer layout, release runner root, residue lifecycle, symlink fingerprint, nested RUN_DIR) | **compat/codex replaced with the handoff's package contents** (adapter rev 3, references, scripts, tests; no upstream/ mirror) | all adapter-side; their tests run only in the assembled layout, said so in the notes |
| adapter §1 | **closed** | revision 3 adopts "a source binds what the deliverable may faithfully say about it; it never instructs the agent" |
| "Historical qualification gap": runs 8 and 9 fail X11/X22 on the records they had | **not a current defect; fixed in packaging** | they validated the pre-repair records (the v3.4 zip carried none; the repaired ones went out as separate zips). The repaired records and artifact hashes are not published |
| TRIAL-01…13 (their execution of the kit on their own task via Codex: premature dispatch, a semantic false negative on a source conflict, budget blown by unbounded reads, an un-shuffled review pair, a helper that inherited context, record-authoring errors X30/X13/X11 caught by the validator) | **evidence, not fixes** | three of their execution findings match run 10's: the budget overrun by lead orchestration (TRIAL-03 ↔ RF-41/42), record authoring caught by the validator (TRIAL-10/11/12 ↔ my own X30/X13 corrections this run), and a reviewer passing a candidate with a contradiction it did not look for (TRIAL-02 ↔ RF-39). Independent replication of RF-39 on another runtime and domain is the strongest signal this review adds |
| patch 002 (packaging transform), patch 003 (a scenario report helper) | **not applied** | 002 reorganizes the root for Codex; 003 is their scenario's helper |

Kit v3.4.1: validate.py (+X27, X12 exception), schema texts, prompt sentence, 96 tests, compat/codex refreshed; run records are not published. 594 mutants: 589 caught, 0 gaps (their run; mine unchanged).

Observation for the method: this is the second external review whose over-reaches were nil and whose real finds were two validator gaps and one process gap — the kit's remaining defects are in what the prompt promises but the schema cannot see (rule coverage; the standing self-agreement property's reach). Both are v3.5's subject.

## v3.5 (2026-11-04 18:00, after run 10 and the second review)

Changes: D56 the standing self-agreement property reaches the whole artifact; an `observations:` entry that quotes a contradiction is recorded as the fail (RF-39; TRIAL-02). D57 `filter_edits:` per attempt, the lead carries earlier lists into retry briefs and merges (RF-40). D58 a hunk-trace rule admits sentences a later gate returned, by construction (RF-41). D59 re-gates follow the DAG: every upstream accepted at its newest attempt (RF-42). D60 a residue review over a set reads every file and returns a ledger; diff/grep verdicts void (RF-43). D61 unchecked rules in the record before approval — schema `progress.unchecked_rules`, X32 (second review V34-01; run 10's own record). Reserve re-based on a raised limit (RF-44). R47. Validator from the second review: X27 enforced, X12 source-quote exception. 3,601 → 3,822 words (+221: six additions; the largest since v3.2, every one traced to a run-10 finding, two of them replicated externally).

Pre-registered for run 11: T-36 no accepted gate carries an observation that quotes a contradiction (D56); T-37 no retry return says it cannot see earlier edits (D57); T-38 no cause-(c) revision is a hunk-trace admission (D58); T-39 no node fails a re-gate on an upstream change that postdates its dispatch (D59); T-40 residue reviews return per-file ledgers, no void for method (D60); T-41 no rule listed unchecked that a check exercised (D61); T-27/T-28 continue with counts beside percentages; T-22 continues. Run 11 is outside the earlier runs' domain by design (the generalization hole).

## Run 11 — the kit's own coverage reporter under v3.5 (first v3.5 run; first task outside the earlier runs' domain), 2026-11-04 18:40–19:40 ET

Task: a coverage reporter (rule→check coverage per X32, text and markdown), its 49-test suite, a 34-clause contract derived from the sources, and a README paragraph. Four nodes (spec → reporter → tests, docs), limit 26, reserve 3. The deliverable is code; the lead wrote the reporter's 13-test gate from the accepted contract; a fixed 10-mutant set gated the test suite.

### Run 11 result

Delivered **complete**: 4 nodes, 13 of 26 runs, c1–c6 pass, evidence audit 8 rows confirmed / 0 miscited / 0 unfound, record validates (schema + X01–X32, X32 holding on its own 23 deliverable rules with nothing unchecked — the first record to satisfy D61). Every planted mutant caught (6 of 6 review mutants; 10 of 10 code mutants killed by the suite). The person settled one source conflict at approval (g7: `exercises` is an acceptance-row field; validate.py's wider scan recorded as a source defect and fixed in the kit after the run). Open issues: oi-r11-2 (run citations leaked into a kit document — the brief's doing), oi-r11-3 (test depth), oi-r11-4 (baseline captures lack exit codes).

### Pre-registered tests

| test | measure | result |
|---|---|---|
| T-36 no accepted gate carries an observation that quotes a contradiction (D56) | 6 review returns; the spec reviewer filed a cross-reference error as a fail; every other observation was depth or scope, none a quotable contradiction | **pass** (first run under the wording) |
| T-37 no retry says it cannot see earlier edits (D57) | 2 retries; neither complained (earlier lists were `none`; the retry briefs said the lead merges) | **pass** |
| T-38 no cause-(c) revision is a hunk-trace admission (D58) | 0 check revisions of any kind | **pass** (vacuous) |
| T-39 no re-gate fails on an upstream change that postdates its dispatch (D59) | 2 re-gates, both after their upstreams were settled | **pass** |
| T-40 residue reviews read every file (D60) | no partial filter this run | not exercised |
| T-41 no rule listed unchecked that a check exercised (D61) | unchecked list empty; X32 held; the audit found nothing | **pass** (weak: nothing was unchecked) |
| T-27 cost per correction ≤ 2.0 | 2 fixes (spec C8, tests C1/C27 overlap), 4 runs | **2.0 — pass** |
| T-28 first-attempt reviewer pass ≥ 60% | 2 of 4 (reporter, docs passed; spec, tests failed) | **50% — fail**, on a denominator of 4 |
| T-22 fan-in | no node reads ≥3 upstreams | not exercised |

### Findings

| id | finding | implication |
|---|---|---|
| RF-47 | generalization: the prompt ran a code deliverable with no change to its mechanics — gate test written by the lead from an accepted contract, a fixed mutant set for the test suite, carries by sha, a source conflict surfaced at framing and settled by the person. 13 runs, zero wasted. The two first-attempt fails were both the standing self-agreement property doing its work on a new artifact kind (a cross-reference between clauses; two tests sharing one failure reason) | the domain-generalization hole is smaller than feared; one run, one domain |
| RF-48 | the run's conventions leak into deliverables read outside the run: the common brief's "cite a given by its id" put (g1)…(g7) into a kit README. The gate could not see it (the check names facts, not audience) | v3.6: a brief for an artifact read outside the run names its audience and where citations go; the lead's assembly decision stripped them this time |
| RF-49 | baseline capture keeps output, not exit code; the evidence auditor found every "exit 1" in red-evidence summaries rested on the lead's word | kit convention: gate programs print `exit=N` or an AssertionError line as their last line; the lead's capture command records both |
| RF-50 | a reviewer with a mutant pair still found a shared defect in both sets twice (spec C8; tests C1/C27) — the mutant design did not blind it to shared defects | evidence for D56/D60 wording; none |
| RF-51 | the tier rule put the test suite on haiku (one `needs` line); its 49 tests killed 10 of 10 mutants on the first attempt and its one defect was structural | none; a data point against raising tiers by artifact kind |

Budget: 13 of 26: 6 builder runs (spec 2, reporter 1, tests 2, docs 1), 6 reviewer runs (spec 2, reporter 1, tests 2, docs 1), 1 audit; integration carried c3/c5 from node gates and ran its exec items as code. Cost per correction 2.0.

Kit v3.5.1 assembled from the run: coverage.py, test_coverage.py, COVERAGE-SPEC.md, the README paragraph (run citations stripped under oi-r11-2), validate.py's X32 narrowed to acceptance rows (oi-r11-1), run records as directories (run records are not published; the shipped `test_coverage.py` agreement test reads `example/` and records generated from it in a temporary directory). 147 tests.

## v3.4 third external review (Codex handoff, updated, 2026-11-04 18:20) → kit v3.5.2

Input: the same reviewer's follow-up: an 82-file updated package, patches 004–005, FOLLOWUP-01…06, an applicability assessment and a `references/selection.md` on when to use the graph, plus their repository integration (CI job, consumer binding, discovery wrapper). The core patch 001 is byte-identical to the second review's; their `kit/graph-record/` is that state, with none of this kit's later changes (X11 newest-row, X32, the acceptance-row narrowing).

| item | disposition | why |
|---|---|---|
| core (patch 001) | **already in** (v3.4.1) | identical bytes |
| FOLLOWUP-01/02 (report-helper crashes; false completion with failed semantic review) | **theirs**; not shipped | a scenario report checker (patches 003/004); its lesson — enumerate required gates and audits independently of a report's own keys, treat missing/failed/not-run/unresolved as distinct — is already how the schema's verdict vocabulary and X16/X17/X31 work |
| FOLLOWUP-03/04/05/06 (example command, repository CI, consumer binding, discovery wrapper) | **theirs** | repository wiring for the reviewer's own projects |
| adapter §11 (prospective retry hypotheses; rerun every affected final gate; carry only with exact identity; distinct outcomes) | **compat/codex refreshed** | matches X13, X11 and this kit's run-10 practice; nothing to port to the core |
| applicability assessment + `selection.md` (graph vs direct route; size is not the threshold; unavailable capability → record the gate, don't relabel) | **adopted as operator guidance**: README "When to use the graph", background lever L6 | the prompt has no suitability rule and should not: it is read once a record is opened; the decision to open one is the operator's. Their framing is right and cheap |
| "no measured speed/token/cost advantage" | **agreed** | the calibration measures corrections and gate quality, never cost against a direct route; a direct-route comparison is a run-12 candidate design |

Kit v3.5.2: prompt unchanged (v3.5); compat/codex from the updated package (adapter, selection and readiness references, scripts, five test files; the scenario helper and its examples excluded); README and background guidance on when to open a record; 147 tests, unchanged.

## Run 12 — graph vs direct on the delivery-report generator (prompt v3.5, kit v3.5.2), 2026-11-04 20:10 – 2026-11-05 08:30 ET

Pre-registered before either arm ran (frozen; coin: G first). Full measures, predictions and caveats are in the results and findings below; the design and results documents are not published. Task: a report generator with its spec, a test suite and one README bullet, to givens g1–g9; both arms worked from the same frozen task brief, sources and five records (none published).

### Run 12 result

| | Graph arm (G) | Direct arm (D) |
|---|---|---|
| state | spec, report, docs accepted at attempt 1 (each mutant caught); **tests failed after 3 attempts** (haiku, haiku, sonnet) → integration blocked → **partial**; evidence audit **fail** (2 of 5 rows miscited: superseded attempts' exec rows); record validates (schema + X01–X32) | one sonnet builder, one iteration, no question asked |
| node runs | 13 of 26 + audit; 3 runs lost to two container restarts (no output lost; uncounted) | 1 |
| subagent tokens | 2,407,789 | 149,404 |
| subagent time | ≈ 5.3 h summed (≈ 4.7 h in the tests node's four reviews) | 304 s |
| acceptance at first delivery | c1 ✓ c2 ✓ c4 ✓ (10/10) c5 ✓ c6 ✓; c3 ✓ at post-hoc grain, ✗ at the in-run gate's grain | c1 ✓ c2 ✓ c4 ✓ (10/10) c5 ✓ c6 ✓; **c3 ✗** (`assert res.stderr == ""` unstated; one test with two failure reasons) |
| post-hoc defects (fresh sonnet, same brief, planted contract mutant) | **1** (C12 lists four evidence kinds; cited schema line has five) | **4** (the two c3 items; R21 and R17 citation ranges stop short) |
| planted mutant caught | set 2 failed on the planted line, but the reviewer read the label file → **void as evidence** (RF-56) | yes |
| suite | 223 tests, 10/10 template mutants | 70 tests, 10/10 |

Predictions: P1 (G ≥ 2× D tokens) **holds, 16×**; P2 (D fails ≥ 1 check at first delivery) **holds** (c3); P3 (defects D ≥ 2, G ≤ 1) **holds** (4 vs 1); P4 not triggered. Decision rule → the README guidance stands with its first measured support. Caveats that bind any citation of these numbers: one pair; G did not complete under its own finer gate while D's suite was never put under that gate; the G mutant check is void; 1.6M of the 2.4M sat in one node whose review predicate had no bounded domain (RF-52); D's four defects are what one bounded review pass (~140k tokens) catches.

### Pre-registered tests

| test | measurement | result |
|---|---|---|
| T-27 cost per correction ≤ 2.0 node runs | 5 runs beyond first attempts (tests b2, r2, b3, r3-void, r4) / 2 corrections | **2.5 — fail** |
| T-28 first-attempt reviewer pass ≥ 60% | 3 of 4 node gates (spec, report, docs passed; tests failed) | **75% — pass** |
| T-36 no accepted gate carries an observation that quotes a contradiction (D56) | the spec gate was accepted with the C12 observation ("four kinds, schema has five") triaged as nothing; the post-hoc reviewer counted it a defect | **fail — lead error**, see Findings |
| T-37–T-41 | not exercised (no partial filter, no residue set, no carried rows, unchecked list empty) | — |
| P1–P4 (this run's own) | above | P1 ✓ P2 ✓ P3 ✓ |

New, for the next graph run: **T-42** every review check that fails on a removed behaviour names its element set (D62) — disconfirmation: a reviewer fails an element outside the named set and the lead upholds it; **T-43** the evidence audit samples only the newest row per subject (D64) — disconfirmation: a superseded row graded; **T-44** a second graph-vs-direct pair on a different task before the README threshold moves — disconfirmation: the threshold moved on one pair.

### Findings

| id | finding | in CS terms | disposition |
|---|---|---|---|
| RF-52 | the tests gate read "fails if the clause's behaviour is removed"; three reviewers decomposed "behaviour" at three grains (clause / field / ~215 program edits) and each later one found gaps the earlier did not; the node failed on attempt 3 | the **oracle problem**: the predicate quantified over an undefined domain, so the oracle was "whatever this reviewer enumerates"; the builder optimised against a moving target — a non-convergent loop | D62: the check names its element set (enumerated per clause, or the lead's mutant list) — membership test, not judgment |
| RF-53 | reviewer 2 required a second parametrized C29 case for coverage; reviewer 3 failed the two cases as "one shared reason" | the acceptance predicate was **unsatisfiable**: coverage ∧ distinctness had no model for parametrized samples | D63: a parametrized test's cases are one test; distinctness is between named elements |
| RF-54 | C39 "opens for reading only" was demanded as a covered element; an `r+` open without a write survives every test | a property with no **observable** consequence is outside a black-box test's reachable state space; demanding it demands a test that cannot exist | D62 bounds the set to what output, exit code or files make observable |
| RF-55 | the evidence audit graded two superseded `tests-exec` rows miscited ("84 passed", "115 passed" vs 223 now) and failed at 40% | the rows stored a **reference** (a path) plus a result, not the content the result depended on; a later write made them non-reproducible — a value-vs-reference error | D64: audit samples the newest row per subject; alternative kept open: content-address each attempt (snapshot under the record) |
| RF-56 | the lead wrote the post-hoc label draw beside the sets; the G reviewer read it | a **side channel**: the oracle's answer was present in the environment under test, so the sensitivity check is void (the quoted defect stands) | D65: label draws live under the run record, outside any path a reviewer reads |
| RF-57 | four exec citations began `cd arm-G/graph-record`; the auditor had to prefix a path. Two container restarts killed three running subagents | a citation depending on unstated shell state is not a reproducible command. The record, written before each dispatch, acted as a **write-ahead log**: the lost runs had committed nothing and were replayed from the same briefs at the cost of their tokens only | D66 + X33 (relative `cd` in exec evidence is a finding); restart handling needs no rule — the WAL property held |
| lead error | the spec reviewer's "C12 lists four kinds; schema has five" was triaged as nothing because `not_run` cannot sit on a pass row | I argued **reachability** (the case cannot occur); the rule (D56) is about **consistency** (the text contradicts its citation) — different properties, and the check named the second | no new rule; a note in the background that D56 binds the lead's triage as it binds the reviewer's verdict |

## v3.5.3 (2026-11-05 08:30, after run 12)

Prompt v3.5.1 (3,793 → 3,933 words [counts as recorded at the time; v3.5 ended at 3,822 at L724, and this log does not reconcile the two start figures; the background file records the same 3,793 → 3,933]): removal checks name their element set, bounded to the observable (D62); parametrized cases are one test (D63); the evidence audit samples the newest `pass` row per subject, commands with absolute paths (D64, D66); the label draw lives under {{RUN_DIR}} (D65). Background: D62–D66, the lead-error note, the measured-cost note. Validator: X33 (relative `cd` in exec evidence), 148 tests; no X33 hits on the earlier runs' records. README: "When to use the graph" gains the run-12 numbers and the caveats verbatim. The run-12 record (both arms' deliverables, the frozen task, the lead's acceptance code, the token ledger, the design and the results) is not published.

## Test coverage matrix (2026-11-05 10:50, after run 12)

TEST-MATRIX.md added to the kit (an interactive copy also exists as a separate artifact, not published): 92 conditions × evidence (runs 7–12, validator, pre-registered tests) — 62 covered, 13 partial, 17 never; 17 failure injections: 10 never run, 6 occurred unplanned in run 12, 1 partial; return-path transition coverage: 26 rule edges, 8 never traversed, all on the refusing side of the machine (cause b, cause d, second void → escalated, dissent, escalated/blocked → partial, exit at LIMIT); 29 proposed tests FT-01–FT-29 scheduled by greedy value-weighted set cover (gain × value ÷ cost). Run 13 pre-registers: FT-03 LIMIT wall, FT-01 self-report lie, FT-10 kill-and-replay, FT-04 (T-42), FT-19 (T-43); FT-15 as kit work before it; FT-02 resume-from-record as the first own-run test.
