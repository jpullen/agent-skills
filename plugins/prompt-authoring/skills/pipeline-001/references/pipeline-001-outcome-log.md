# PIPELINE-001 Outcome Log

> **Purpose.** Outcome-measurement substrate for PIPELINE-001 (see `docs/reference/rule-design-standards.md` § Pipeline Registry and `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § G5). One row per rule authored via PIPELINE-001; row evolves as the rule is revised, retracted, or silently ignored.

**Status:** Living | **Created:** 2026-05-13 | **Cadence:** append-on-authoring; revise-on-modification

---

## How to use this file

Add a new row every time a PIPELINE-001-authored rule lands (the commit body must reference this file). Revise an existing row when the rule is modified, retracted, or observed to be silently ignored — update `first-revision-date`, `retraction-date`, or `silent-ignore-evidence` accordingly. The `pipeline-verdict` column records the Stage 7 final verdict **at authoring time** and is never retroactively updated when the rule is later revised; revisions go in `notes` and the revision-date column. Append a provenance paragraph below each new row at time of insertion.

---

## Falsification criterion (RULE-010)

At N ≥ 30 per group (post-pipeline vs. pre-pipeline rules), if revision rates are comparable, PIPELINE-001 does not earn its overhead. Until N ≥ 30, this file produces **descriptive** observations only — no inferential claims. Per CLAUDE.md plan-design gate `[GATE-PLAN-SAMPLE-SIZE]`.

---

## Kill criterion

If fewer than 5 new PIPELINE-001-authored rules accumulate in 90 days, the lineage log is underpowered indefinitely; switch to within-rule case studies per the plan's § C1 specification. Re-evaluate this kill criterion at 2026-08-11 (90 days from creation).

---

## Coordination

- `T5.35` (retrofit historical rules with pipeline-style authoring records) — backlog item; orthogonal. When T5.35 runs, its output populates the § Pre-pipeline cohort section below.
- `T5.37` (prior-art currency gate, 90-day staleness) — backlog item; coordinate timing if both produce N-based studies that draw on overlapping rule populations.
- `[PIPELINE-001-2B-REPLAY]` — backlog item; the 20-output Stage 2b.1 replay study; orthogonal to lineage but uses same N-based framing and similar inter-rater methodology.

---

## Lineage table

| rule-id | authored-date | pipeline-verdict | first-revision-date | retraction-date | silent-ignore-evidence | notes |
|---------|---------------|------------------|---------------------|-----------------|------------------------|-------|
| Stage 7 termination bound (S7-BOUND) | 2026-05-12 | PASS | 2026-05-16 | NULL | NULL | Closes G4 from critique-of-pipeline-001 plan; commit `db15cb7`; test 6/6. **Revised 2026-05-16 (v2.8.7):** the 3-iteration bound was the original design but its numeric literal lacked calibration source (FB-005); FB-044 (RCA on FB-005) replaced the bound with Primary + Dissent capture (no iteration cap; ESCALATED narrowed to degenerate exits). The rule's *intent* (termination semantics for Stage 7) survives; the *mechanism* changed. Test count: 6/6 → 8/8. |
| `[RULE-P04]` Critique grounding | 2026-05-12 | PASS | NULL | NULL | NULL | Closes G6 from critique-of-pipeline-001 plan; commit `db15cb7`-era (test added in same plan window); test 18/18. |
| `[RULE-P03]` Stage execution isolation | 2026-05-13 | PASS | NULL | NULL | NULL | Closes G1 + subsumes G3 from critique-of-pipeline-001 plan; commit `06bfd70`; test 26/26. First rule to be authored by an isolated subagent per its own per-target table (canonical self-application). |
| Citation-existence linter (Stage 7c test-tier promotion) | 2026-05-13 | PASS | NULL | NULL | NULL | Plan § Phase B → B2; commit `b8beaf3`; test 12/12. Promotes Stage 7c from author-discipline-tier to test-tier on Local + Remote (Claude Chat retains author-discipline). Surfaced 5 reference-hygiene bugs filed as `[PIPELINE-001-7C-SMOKE]`. |
| Stage 2b.1 — Independent retrieval verification | 2026-05-13 | PASS | NULL | NULL | NULL | Closes G2 from critique-of-pipeline-001 plan; commit `dd4a16d`; test 34/34 (initial 31/34 due to pre-existing working-tree state from prior partial attempt). Replay-study deferred as `[PIPELINE-001-2B-REPLAY]`. |

---

## Backfilled rules (PIPELINE-001 cohort to date)

### Stage 7 termination bound (S7-BOUND)

Origin: closes G4 ("Stage 7 BLOCKED/CORRECTED loop has no termination bound") from `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md`. Before this rule, the Stage 7 verdict block read "Loop until PASS" with no max-iteration bound; pathological runs could churn indefinitely between Stage 6 and Stage 7. The original rule (v2.8.2, 2026-05-12) added a three-return limit producing a `VERDICT: ESCALATED` exit with full check trace, gated on a human-override note in the plan's verification log before IMPLEMENTED. Test evidence: `tests/test-pipeline-stage7-termination.sh` 6/6 assertions passing (started 5/6 failing); TDD-driven with a fixture simulating three CORRECTED returns without PASS. Propagation: RULE-028 permitted-values list updated to include ESCALATED, changelog v2.8.2 in `docs/reference/rule-design-standards.md`; no anomalies reported during initial authoring.

**Revision 2026-05-16 (v2.8.7):** the 3-iteration bound was a numeric literal without calibration source — flagged by FB-005 in the walkthrough Round 1 review and routed to FB-044 (RCA on FB-005) in Round 2. The bound is replaced by **Primary + Dissent capture**: the CORRECTED/BLOCKED → Stage 6 → re-run-Stage 7 loop now has no iteration cap; it terminates at PASS, at PRIMARY+DISSENT (stable disagreement captured with both positions), or at ESCALATED (narrowed to degenerate exits — Stage 7 cannot produce any verdict). The rule's *intent* (Stage 7 has named terminating conditions, never silent infinite loop) survives intact; the *mechanism* changed. Test extended to 8 structural assertions (5/8 → 8/8 after the rewrite). Hypothesis on the original bound (v2.8.2) marked superseded; new hypothesis declared on Primary + Dissent capture (disconfirmation = 20-run replay showing PRIMARY+DISSENT artifacts have higher post-implementation revision than PASS artifacts). This is the first lineage-row revision in the post-pipeline cohort and exercises the schema's `first-revision-date` column.

### `[RULE-P04]` Critique grounding

Origin: closes G6 ("Adversarial-critique-must-quote is unwritten") from the critique-of-pipeline-001 plan. Before this rule, critique-shaped artifacts (headings containing `critique`, `review`, `assessment`, `evaluation`, `audit` of a named internal target) had no quoting obligation — the pasted external critique that triggered the plan is the existence proof, citing zero verbatim quotes from the standards while reinventing Stage 2b / RULE-P02 / RULE-031. The rule mandates a `Verbatim quotes:` field (≥3 quotes with section/line refs) or `None — target is sequestered per RULE-P02`. Test evidence: `tests/test-rule-p04-critique-grounding.sh` 18/18 structural assertions passing; one test-authoring anomaly resolved (awk range-extraction end-pattern collapsed to one line because `^### ` matched the start heading; switched to `^### Control Levers`). Self-application clean: the authoring plan quotes Stage 2b line 107, Stage 7 line 204, and RULE-P02 lines 275–278 verbatim — satisfying its own rule on its own authoring artifact.

### `[RULE-P03]` Stage execution isolation

Origin: closes G1 ("Execution-mode isolation is unstated") and subsumes G3 ("Stage 5 evaluator-not-designer is unenforced") from the critique-of-pipeline-001 plan. Before this rule, RULE-P01 / RULE-P02 / RULE-031 governed artifact shape and infrastructure availability but not execution mode — a single Agent invocation on Claude Code could satisfy every existing rule while running all 7 stages in one model context, satisfying sequestration at the prompt level only. The rule mandates an `Execution context:` field on every stage invocation with three permitted values and a per-target table (Local / Remote / Claude Chat). This is the first PIPELINE-001-authored rule that was itself authored by an isolated subagent per its own per-target table — canonical self-application. Test evidence: `tests/test-rule-p03-execution-isolation.sh` 26/26 assertions passing (started 3/26); regression clean on P04 (18/18) and S7-BOUND (6/6). A notable anomaly: both the v2.8.2 and v2.8.3 changelog entries had misclassified Mobile as `Claude Chat / Sequential same-context — degraded execution`; the authoring subagent identified both and corrected them in the same commit, and filed a process anti-pattern entry in `docs/reference/project-anti-patterns.md` ("Claude Code Remote (Mobile / Web) conflated with Claude Chat in per-target reasoning").

### Citation-existence linter (Stage 7c test-tier promotion)

Origin: plan § Phase B → B2, salvaging a narrowed thread from the pasted critique's recommendation #1. The rule is not a governance rule in the RULE-NNN sense but a tooling artifact (`tools/check-citations.py`) that promotes Stage 7c's citation-existence check from author-discipline-tier to test-tier enforcement on Claude Code Local + Remote (Claude Chat retains author-discipline per RULE-031). Before this tool, Stage 7c's `Enforced by:` field named only author discipline; the linter adds mechanical resolution of `[file:line]`, markdown link, and `RULE-/ERR-/PIPELINE-/T5.` ID references. Test evidence: `tests/test-citation-linter.sh` 12/12 assertions passing (started 3/12); TDD-driven with a broken-fixture failing before implementation. Smoke-check anomaly: the linter surfaced 5 genuine reference-hygiene bugs filed as `[PIPELINE-001-7C-SMOKE]` and one known v1 limitation (false positives on placeholder tokens in backtick/code-block contexts) filed as `[PIPELINE-001-7C-LINTER-V2]`.

### Stage 2b.1 — Independent retrieval verification

Origin: closes G2 ("Stage 2b is self-attested") from the critique-of-pipeline-001 plan. Before this stage, Stage 2b's prior-art convergence check was performed by the same LLM that produced the rule under review, sharing training-time priors — the independence of the verifier was the gap, not the absence of the check. Stage 2b.1 adds a structurally isolated subagent (per RULE-P03) that takes Stage 2b's convergence-map rows as input and emits per-row `CONFIRMED` / `MISCITED` / `UNFOUND` verdicts. The 20-output replay measurement study (which would produce the falsification evidence for the hypothesis that self-attestation inflates convergence scores) was deferred as `[PIPELINE-001-2B-REPLAY]` per CLAUDE.md plan-design gate `[GATE-PLAN-SAMPLE-SIZE]`. Test evidence: `tests/test-pipeline-stage-2b1-independence.sh` 34/34 assertions passing (initial 31/34 — the Stage 2b.1 body was pre-existing in the working tree from a prior partial attempt; the authoring task closed the remaining 3 by adding Stage 7 sub-check 7f, updating the Stage 7 self-check line, and adding the v2.8.6 changelog entry); this pre-existing-state anomaly was surfaced in the plan-completion ceremony triple-loop.

---

## Pre-pipeline cohort (control group, for revision-rate comparison)

N=0; populated by T5.35. This section will hold rows for rules authored before PIPELINE-001's formal activation (RULE-001 through RULE-024, RULE-P01, RULE-P02) once T5.35 retrofits them with pipeline-style authoring records. Revision-rate comparison against the post-pipeline cohort above is the primary inferential use of this section; comparison is only meaningful at N ≥ 30 per group per the falsification criterion above.

---

## Changelog

v1.1.0 — 2026-05-16: File renamed from `rule-lineage.md` (original name implied project-wide scope; content is PIPELINE-001-specific). Title updated to "PIPELINE-001 Outcome Log". Inbound references in `error-catalog.md` and `framework-backlog.md` updated to the new path. Per FB-047 (walkthrough Round 2 RCA on FB-023). Stage 7 termination bound row revised in v2.8.7 of rule-design-standards.md — see § Backfilled rules § Stage 7 termination bound (S7-BOUND).

v1.0.0 — 2026-05-13: Initial creation. Schema defined; five rules backfilled (Stage 7 termination bound, RULE-P04 Critique grounding, RULE-P03 Stage execution isolation, citation-existence linter, Stage 2b.1 independent retrieval verification). Execution context: Isolated subagent — fresh context (sonnet tier, Claude Code Remote per RULE-P03 Remote row). Descriptive label applied per CLAUDE.md plan-design gate `[GATE-PLAN-SAMPLE-SIZE]`; kill criterion re-evaluation date 2026-08-11.
