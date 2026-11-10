---
name: pipeline-001
description: Run a staged structured analysis (frame, route expertise, check prior art, analyze, synthesize, adversarial critique, refine, coherence review) on a substantive analytical or design problem where a single prompt would give shallow or over-confident output.
disable-model-invocation: true
---

# PIPELINE-001: Multi-Stage Analysis Pipeline

## What This Is

A seven-stage structured reasoning pipeline for problems that benefit from disciplined decomposition: frame the problem, route expertise, check prior art, analyze, synthesize, critique, refine, and verify. Each stage isolates a cognitive mode to prevent earlier framing from collapsing later stages into confirmation.

For governance artifacts (guides, rule sets, standards, instruction templates) — artifacts that govern future authoring acts — two additional stages (2b and 2b.1) run a prior art convergence check and independent citation verification before synthesis begins.

**Scope:** This pipeline applies to substantive analytical or design problems where a single prompt produces shallow or over-confident output. It is not appropriate for lookup tasks, factual Q&A, or tasks where the answer is a fact rather than a judgment.

**Sequestration note:** Several stages require isolation from earlier stages' framing — not just their conclusions. Where sequestration is marked, start a fresh context (new subagent or new conversation turn) and pass only the explicitly listed inputs. Passing an earlier stage's reasoning as context defeats the isolation.

---

## Running the Pipeline

Each stage is a standalone prompt. Run stages in order. Pass outputs forward as specified in each stage's carry-forward line.

**Execution context options:**

- **Claude Code (recommended):** Run each stage as a separate subagent call. Each call gets a fresh context window. Pass only the carry-forward content, not the full conversation history.
- **Claude.ai / Claude Chat (advisory mode):** Paste each stage prompt into a new conversation turn, including the carry-forward content from the previous stage. Do not continue in the same turn — start fresh.
- **Stages 2b.1 and 5** require strict sequestration. Always run these in a completely separate conversation or subagent, even if you ran the preceding stage inline.

The pipeline terminates when Stage 7 returns PASS, PRIMARY+DISSENT, or ESCALATED. There is no iteration cap on CORRECTED/BLOCKED loops — fix and re-run Stage 7 until one of the three terminal verdicts is reached.

---

## Stage 1: Problem Framing

```
You are a problem-framing engine.

TASK:
- Restate the problem clearly
- Identify goals, constraints, and success criteria
- List assumptions
- Identify missing or unclear information

INPUT:
[Insert problem]
```

**Required output shape:** Problem statement / Goals / Constraints / Assumptions / Unknowns

**Carry forward to Stage 2:** The complete Stage 1 output.

---

## Stage 2: Expertise Routing

```
You are an expertise router.

TASK:
- Identify 3–6 relevant domains
- Explain why each is needed
- Describe what each contributes

INPUT:
[Stage 1 output]
```

**Required output shape:** Domains / Contributions / Interactions

**Carry forward to Stage 3:** The complete Stage 1 and Stage 2 outputs.

**Governance artifact check:** Before proceeding to Stage 3, determine whether the pipeline output is a governance artifact — a guide, rule set, standard, or instruction template that will govern future authoring acts. If yes, run Stage 2b before Stage 3. If no, record "None — pipeline output is not a governance artifact" and skip Stages 2b and 2b.1.

---

## Stage 2b: Prior Art Convergence Check

*Run this stage only if the pipeline output is a governance artifact. If you recorded the exemption in Stage 2, skip to Stage 3.*

```
You are a prior art researcher for governance artifacts.

TASK:
Your goal is to map proposed rules or structural choices against existing external taxonomies,
standards, and prior work. Do not evaluate the artifact's quality here — only map coverage.

Steps:
1. Generate 4–8 search queries that would surface existing standards, taxonomies, or guidance
   in the same domain as the artifact under review.
2. Execute or simulate those searches. For each result, extract any relevant structural elements
   (categories, rules, requirements, constraints) that overlap with the artifact's scope.
3. Build a convergence map: a table with columns:
      Proposed element | External source | Match type | Notes
   Match types: DIRECT (same element, same semantics) | PARTIAL (overlapping but not identical) |
   ABSENT (proposed element has no external analog found)
4. Identify simplification candidates: proposed elements where external sources offer
   established vocabulary that could replace custom terms.
5. List gaps: external coverage the artifact does not address. Triage each gap as:
   CRITICAL (omission undermines artifact's goals) | INFORMATIVE (worth noting, not blocking) |
   OUT-OF-SCOPE (external standard addresses something the artifact intentionally excludes).
6. Make a decision — one of three:
   - REDESIGN-FROM-TAXONOMY: ≥70% of proposed elements map onto an existing taxonomy.
     Recommend redesigning the artifact starting from that taxonomy rather than the current draft.
   - EXTEND-EXISTING: <70% convergence and the proposed elements meaningfully extend beyond
     external coverage. Proceed with the artifact, documenting divergence rationale.
   - DOCUMENT-DIVERGENCE: Proposed elements map onto external sources but diverge intentionally.
     Record the divergence rationale for each diverging element.

INPUT:
[Stage 2 output — domains and contributions only; do not include the Stage 1 problem statement here]
[The artifact or artifact description under review]
```

**Required output shape:**
- Search queries used
- Convergence map table (Proposed element / External source / Match type / Notes)
- Simplification candidates
- Gaps and gap triage
- Decision: REDESIGN-FROM-TAXONOMY / EXTEND-EXISTING / DOCUMENT-DIVERGENCE, with rationale

**Carry forward to Stage 2b.1:** The convergence map table rows verbatim (not Stage 2b's reasoning or framing). Include the decision verdict.

---

## Stage 2b.1: Independent Citation Verification

*Run this stage only if Stage 2b ran in non-degenerate form (i.e., it did not record "None — pipeline output is not a governance artifact"). If Stage 2b emitted that exemption, also record it here and skip to Stage 3.*

**Execution context:** Always run in a completely fresh context — do not pass Stage 2b's reasoning, framing, or author identity. Pass only the convergence map rows listed below.

- Claude Code: `Isolated subagent — fresh context` — launch a new subagent with only the Convergence map: rows from Stage 2b.
- Claude Chat: `Sequential same-context — degraded execution` — the verifier shares context with the Stage 2b retriever; the verdict is advisory, not dispositive.

*Sequestered: the author/identity who built the convergence map. The verifier does not know whose work it is verifying — pass only the table rows, nothing else from Stage 2b.*

```
You are an independent citation verifier.

TASK:
You have been given a convergence map — a table of proposed elements matched against
external sources. Your job is to verify each row independently, without knowing who
produced the map or why.

For each row in the table:
1. Locate the cited external source independently (do not rely on Stage 2b's description).
2. Verify that the cited source actually contains or supports the claimed match.
3. Assign one of three verdicts:
   - CONFIRMED: The external source contains what was claimed. The match type is accurate.
   - MISCITED: The source exists but does not support the claimed match, or the match type
     is inaccurate.
   - UNFOUND: The source could not be located, or it exists but the cited element is absent.

Produce an OUTPUT table with columns:
   Row # | Proposed element | External source | Claimed match type | Verdict | Verifier notes

Then compute: (MISCITED + UNFOUND) / total rows.
- If ≤ 30%: emit Stage 2b.1 verdict PASS.
- If > 30%: emit Stage 2b.1 verdict BLOCKED and route to Stage 6 before proceeding.

INPUT:
Convergence map: [rows verbatim from Stage 2b, one row per line]
```

**Required output shape:**
- OUTPUT table: Row # / Proposed element / External source / Claimed match type / Verdict / Verifier notes
- (MISCITED + UNFOUND) count and percentage
- Stage 2b.1 verdict: PASS or BLOCKED

**If BLOCKED:** Return to Stage 2b — remediate the failed citations, rebuild the convergence map, and re-run Stage 2b.1 before proceeding to Stage 3. (Stage 6 is not available at this point; the recommendation has not been generated yet.)

**Carry forward to Stage 3:** Stage 2b.1 verdict and the OUTPUT table (for Stage 7 sub-check 7f).

---

## Stage 3: Multi-Domain Analysis

```
You are a multi-disciplinary analysis engine.

TASK:
- Apply each domain identified in Stage 2 to the problem
- For each domain, include: practical constraints, risks, second-order effects, tradeoffs
- Identify patterns that appear across multiple domains

INPUT:
[Stage 1 output]
[Stage 2 output]

PRIORITIES:
[Insert priorities — if none, state: "No explicit priority ordering; weight domains by relevance to the core problem"]
```

**Required output shape:** Insights by domain / Risks / Tradeoffs / Key patterns

**Carry forward to Stage 4:** Complete Stage 1, Stage 2, and Stage 3 outputs.

---

## Stage 4: Synthesis and Decision

```
You are a decision synthesis engine.

TASK:
- Combine the multi-domain analysis into a solution or recommendation
- Prioritize based on the goals identified in Stage 1
- Provide a clear recommendation with explicit reasoning
- State which assumptions the recommendation depends on

INPUT:
[Stage 1 output]
[Stage 2 output]
[Stage 3 output]
```

**Required output shape:** Recommendation / Reasoning / Assumptions

**Carry forward to Stage 5:** The Stage 4 recommendation text verbatim (not the full conversation history — only the recommendation section and its reasoning).

---

## Stage 5: Adversarial Critique

*Run this stage in a fresh context. Do not pass Stages 1–3 — the critique target enters here as the sole input. This prevents Stage 5 from rationalizing the synthesis rather than challenging it.*

**Execution context:** Always run in a completely fresh context — do not pass Stage 4's supporting reasoning, Stages 1–3, or any author identity. Pass only the Stage 4 recommendation and reasoning verbatim.

- Claude Code: `Isolated subagent — fresh context` — launch a new subagent with only the Stage 4 recommendation.
- Claude Chat: `Sequential same-context — degraded execution` — the critic shares context with Stage 4; the critique may rationalize rather than challenge.

*Sequestered: Stages 1–3 and Stage 4's synthesis chain. The critic sees only the recommendation text.*

```
You are a skeptical reviewer.

TASK:
- Identify weaknesses in the recommendation
- Challenge assumptions explicitly — name each assumption and state why it might not hold
- Highlight risks, including second-order and tail risks
- Provide counterarguments to the main recommendation
- For every critique of a specific claim or passage: quote ≥3 verbatim excerpts from
  the recommendation that anchor that critique specifically. Do not generate critique
  that invents content not present in the text.

INPUT:
[Stage 4 recommendation and reasoning — verbatim]
```

**Required output shape:** Flaws / Challenged assumptions / Risks / Counterarguments / Verbatim anchors for each critique

**Carry forward to Stage 6:** Stage 4 output and Stage 5 output together.

---

## Stage 6: Refinement

```
You are a refinement engine.

TASK:
- Improve the recommendation based on the critique
- Address each weakness raised in Stage 5
- Where a weakness cannot be addressed, state it as a remaining uncertainty
- Clarify any ambiguities surfaced during critique

INPUT:
[Stage 4 output]
[Stage 5 output]
```

**Required output shape:** Final answer / Improvements made (mapped to Stage 5 critiques) / Remaining uncertainty

**Carry forward to Stage 7:** The complete final answer from Stage 6, plus the Stage 2b.1 OUTPUT table if Stage 2b ran.

---

## Stage 7: Coherence Review

Run the following five sub-checks in sequence. A single BLOCKED or CORRECTED verdict stops the sequence — fix the issue and re-run Stage 7 from sub-check 7a.

**7a — Section order:** Verify that referenced sections or terms are defined before they are referenced. Flag any forward references to undefined terms.

**7b — Internal consistency:** Verify that no two sections contradict each other. If a contradiction is found, emit BLOCKED.

**7c — Cross-reference completeness:** Verify that every cited document, section, or source exists and that the citation is accurate. If a broken citation is found, emit BLOCKED.

**7d — Document-type fit:** Verify that the document's structure and framing match its declared type (guide, analysis, recommendation, standard, etc.).

**7e — Execution-context consistency:** Verify that every stage `Execution context:` declaration is consistent with the stated deployment target (Claude Code subagent, Claude Chat conversation turn, or other). If an invocation instruction contradicts the deployment target, emit CORRECTED.

**7f — Stage 2b.1 verification table consistency:** If Stage 2b ran in non-degenerate form (i.e., did not record "None — pipeline output is not a governance artifact"):
  - Confirm Stage 2b.1's OUTPUT table is present in the pipeline execution record.
  - Confirm one row per convergence-map entry from Stage 2b.
  - Confirm all verdicts are from {CONFIRMED, MISCITED, UNFOUND}.
  - Confirm the (MISCITED + UNFOUND) percentage is computed and the PASS/BLOCKED threshold is applied correctly.
  - If any of the above fail, emit CORRECTED.
  
  If Stage 2b recorded "None — pipeline output is not a governance artifact," sub-check 7f passes automatically.

**Verdict options:**

| Verdict | Meaning | Next action |
|---|---|---|
| PASS | All sub-checks pass | Pipeline complete |
| CORRECTED | A fixable issue was found | Fix the issue; re-run Stage 7 from 7a |
| BLOCKED | Contradiction or broken citation | Fix the source; re-run Stage 7 from 7a |
| PRIMARY+DISSENT | Stage 7 returns the same BLOCKED or CORRECTED verdict on the same specific issue across two consecutive Stage 7 runs, with Stage 6 re-run in between, and Stage 6's output does not address the flagged issue | Proceed with both positions recorded in the output |
| ESCALATED | Stage 7 cannot produce any verdict | Requires human override to mark the pipeline run complete |

**Termination:** No iteration cap on CORRECTED/BLOCKED loops. The pipeline exits only at PASS, PRIMARY+DISSENT (Dissent position preserved in output), or ESCALATED.

---

## Changelog

- **v1.0.0 (2026-05-18):** Extracted from rule-design-standards.md v2.8.7 (PIPELINE-001-EXTRACT).
