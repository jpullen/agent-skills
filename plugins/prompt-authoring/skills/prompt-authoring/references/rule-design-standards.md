# Prompt Authoring Guide

> For motivation, failure-mode rationale, and design decisions, see [prompt-authoring-background.md](prompt-authoring-background.md).

**Scope:** Durable instructions for AI: `CLAUDE.md`, `SKILL.md` files, active plan files, error catalog entries, experiment contracts, and system prompt files. Behavior-scoped — applies wherever a rule or obligation is authored for AI consumption.

**Out of scope:** archived plans, design documents, templates, populated deployment-context files, test fixtures.

**Enforcement:** Required reading before any of the following:
- `CLAUDE.md` edit (behavioral change)
- `SKILL.md` edit (behavioral change)
- New or modified rule in this guide
- New anti-pattern entry
- New or modified error catalog entry
- New or modified plan template or plan completion procedure
- New experiment contract
- New or modified scope declaration on any rule section

---

## Part 1: Pipeline Design

> See [prompt-authoring-background.md](prompt-authoring-background.md) for why each stage exists.

### Pipeline Registry

Every pipeline definition in this guide carries a stable `[PIPELINE-NNN]` identifier and a canonical name. References elsewhere in the corpus must cite the ID; the canonical name is for readability.

| ID | Canonical name | Trigger condition | Stage count |
|---|---|---|---|
| `[PIPELINE-001]` | Full Pipeline | Stage 2 identifies ≥3 relevant domains; or output will be acted on without human review; or task spans ≥2 rows of the Relationship table | 8 (Stages 1, 2, 2b, 3, 4, 5, 6, 7) |
| `[PIPELINE-002]` | Lightweight Pipeline | Stage 2 identifies <3 domains; or output reviewed by a human before action; or task scoped to a single framework | 5 sequential questions + optional coherence check |

**Adding a new pipeline definition** requires a Full Pipeline (`[PIPELINE-001]`) run on the addition itself, including Stage 2b prior art search and Stage 7 coherence review. New pipelines append rows to this table; IDs are sequential and never reused.

**Selection.** Each stage feeds the next — paste the previous output as `INPUT` for the next stage. Run `[PIPELINE-001]` when any of its trigger conditions are met; otherwise run `[PIPELINE-002]`.

---

> **`[PIPELINE-001]` stage definitions have been extracted to `pipeline-001-prompt.md`.**
> That file is the standalone, exportable specification — use it to run the pipeline in Claude.ai Projects or directly.
> The Pipeline Registry table, `[PIPELINE-002]`, structural rules (RULE-P01 through RULE-P04), and Control Levers remain below as the canonical rule-ID reference.

### [PIPELINE-002] Lightweight Pipeline

*Closed synonym list: Lightweight Pipeline, Lightweight Variant (deprecated synonym retained for backward compatibility). No other terms resolve to this pipeline. Precedence: Lightweight Pipeline preferred when authoring new references; Lightweight Variant retained for citations dated before 2026-05-08.*

**Use when full pipeline conditions are not met** (Stage 2 identifies <3 domains, output will be reviewed by a human before action, or task is scoped to a single framework). Run five questions sequentially:

1. What expertise is needed?
2. Analyze from those perspectives.
3. Give a recommendation based on priorities.
4. What could go wrong?
5. What is uncertain?

**For durable outputs** (committed, shared externally, or acted on without further review): run the coherence check before marking complete. Check four items: (a) no section contradicts another; (b) all cross-references exist and are accurate; (c) sections appear in dependency order; (d) document structure matches its declared type. If any check fails, fix and re-check. Verdict: PASS (all clear) or CORRECTED (fixed — re-check until PASS).

### Cross-stage handoff structure [RULE-P01]

> **Scope:** Process

**Every stage output specification must contain a `Fields consumed by next stage:` line.** Permitted values:
- A list of named fields each value of which is referenced as input by the next stage's TASK block, *or*
- `None — final stage (no consumer)`, *or*
- `None — next stage takes raw output as opaque blob with documented contract`.

Verify by name-matching: for each named input in stage N+1's TASK block, find a matching named field in stage N's `Fields consumed by next stage:` list. If absent, add the field before running the pipeline.

`[Hypothesis: implicit handoffs ("use stage N's analysis," "given the prior output") produce context loss equivalent to lost-in-the-middle across the stage boundary; disconfirmation = a structurally-identical pipeline with implicit handoffs producing comparable downstream coherence to one with named-field handoffs]`.

**Worked example.** Stage 2 (Expertise Routing) produces `Domains / Contributions / Interactions`. Stage 3 (Multi-Lens Analysis) needs per-domain priority weights. Stage 2's output specification:
```
Fields consumed by next stage:
  - Domains: [name, contribution, weight]
  - Interactions: [domain-pair, type]
```
Implicit weights inferred from prose are the most common cross-stage loss.

Trigger features: any pipeline stage specification containing a "Required output shape:" or "Output shape:" line; presence of stage labels (`Stage N`, `Framing`, `Routing`, `Analysis`, `Synthesis`, `Critique`, `Refinement`) in a prompt template; or `None — single-stage prompt with no downstream consumer stage`.

Borderline cases:
- Stage 2 (Expertise Routing) produces `Domains / Contributions / Interactions` and Stage 3's TASK references "the domains and their weights" — in-scope; implicit handoff detected; `Fields consumed by next stage:` list required naming `Domains: [name, contribution, weight]`.
- A standalone single-prompt request with a named output shape and no downstream stage — out-of-scope; `None — final stage (no consumer)` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every stage output specification` is bare; `Fields consumed by next stage:` permitted values include `None — final stage` and `None — opaque blob` for non-handoff cases.*

### Adversarial sequestration [RULE-P02]

> **Scope:** Process

**Every pipeline INPUT block must contain a `Sequestered:` line.** Permitted values:
- A list of candidate solutions evaluated downstream that are deliberately absent from this stage's input, *or*
- `None — no downstream evaluation stage in this pipeline`, *or*
- `None — this stage IS the evaluation stage (candidates introduced here as input)`.

The line forces the author to confront whether candidates are leaking into a generation stage and proves the absence visibly.

`[Hypothesis: visibility of a candidate during generation produces convergence on that candidate even when the generation stage is instructed to ignore it; disconfirmation = a generation stage with the candidate visible producing solutions that diverge from the candidate at a rate comparable to a sequestered generation stage]`.

**Worked example.** A pipeline asks Stage 4 (Synthesis) to evaluate a pre-existing IA proposal. Stage 1 (Framing) INPUT block:

```
INPUT:
  Problem: <description>
  Sequestered: the IA proposal under evaluation (introduced at Stage 4)
```

Stage 1 sees the problem only; the candidate enters at Stage 4 and the adversarial-critique stage. The `Sequestered:` line documents the choice in the artifact.

Trigger features: `INPUT:` keyword followed by content in a pipeline prompt template; presence of stage labels preceding a generation or synthesis task; multi-stage prompts where one stage produces candidates evaluated by a downstream stage; or `None — single-stage prompt with no generation/evaluation split`.

Borderline cases:
- A pipeline where Stage 1 (Framing) receives the IA proposal text and Stage 4 (Synthesis) evaluates it — in-scope; Stage 1 is a generation stage; `Sequestered: the IA proposal under evaluation (introduced at Stage 4)` required in Stage 1's INPUT block.
- Stage 5 (Adversarial Critique) INPUT block — `None — this stage IS the evaluation stage` permitted value applies; candidates are introduced here as input.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every pipeline INPUT block` is bare; `Sequestered:` permitted values include `None — no downstream evaluation stage` and `None — this stage IS the evaluation stage` for non-generation cases.*

### Stage execution isolation [RULE-P03]

> **Scope:** Process

**Every pipeline stage invocation must contain an `Execution context:` line.** Permitted values:
- `Isolated subagent — fresh context, INPUT block is the only carried state` (default on Claude Code Local and Claude Code Remote), *or*
- `Sequential same-context — degraded execution, candidates leak across stages` (sole permitted value on Claude Chat; downgrades downstream `Decision:` and `Verdict:` fields to advisory), *or*
- `None — single-stage prompt with no inter-stage execution mode question`.

RULE-P01 governs the *shape* of cross-stage handoffs and RULE-P02 governs the *visibility* of candidates in stage inputs — both at the artifact-shape level. Neither governs the *execution mode* of the stage itself. A single-context run can satisfy every RULE-P01 / RULE-P02 obligation at the prompt level while the model retains full memory of all prior stage outputs, producing per-stage convergence on a single reasoning trajectory. The `Execution context:` line makes the execution mode surface-checkable, so the artifact records which isolation guarantee the run actually had.

`[Hypothesis: same-context execution produces inter-stage convergence on a single reasoning trajectory irrespective of RULE-P02 sequestration; disconfirmation = comparable Stage 5 / Stage 4 divergence rates between same-context and isolated-subagent runs on a 20-pipeline replay]`.

**Per-target table.**

| Deployment Target | `Isolated subagent` available | Default when unspecified |
|---|---|---|
| Claude Code Local | Yes (Agent tool, worktree isolation) | `Isolated subagent — fresh context` |
| Claude Code Remote (Web + Mobile) | Yes (Agent tool, sequential subagents per CLAUDE.md § Subagent Execution) | `Isolated subagent — fresh context` |
| Claude Chat | No (no Agent tool, single-context only) | `Sequential same-context — degraded execution` (downgrades `Decision:` and `Verdict:` to advisory) |

**Worked example.** A `[PIPELINE-001]` run authoring a new rule launches Stage 4 (Synthesis) on Claude Code Local. The Stage 4 invocation header:

```
INPUT:
  Stage 1 / 2 / 2b / 3 output: <pasted>
  Sequestered: the candidate solution under evaluation (introduced at Stage 5)
  Execution context: Isolated subagent — fresh context, INPUT block is the only carried state
```

Stage 5 (Adversarial Critique) then runs in a separately-spawned subagent — not the same context that produced Stage 4 — so the critique stage does not inherit Stage 4's framing. The `Execution context:` line records that the isolation guarantee held; a same-context follow-on would record `Sequential same-context — degraded execution` and downgrade Stage 5's `Decision:` and `Verdict:` fields to advisory per the Claude Chat row.

Trigger features: any pipeline stage specification containing a `TASK:` or `INPUT:` block; presence of stage labels (`Stage N`, `Framing`, `Routing`, `Analysis`, `Synthesis`, `Critique`, `Refinement`) in a prompt template; or `None — single-stage prompt with no downstream consumer stage`.

Borderline cases:
- A `[PIPELINE-001]` run on Claude Code Remote (Mobile or Web) launching Stage 5 via the Agent tool — in-scope; Remote row's default applies; `Execution context: Isolated subagent — fresh context` required. The Mobile constraint is *operational* (sequential subagents, one at a time per CLAUDE.md) not *structural*; the artifact-shape declaration is identical to Local.
- A `[PIPELINE-001]` run on Claude Chat where the author pastes Stage N's output into Stage N+1's prompt within the same conversation — in-scope; Claude Chat row applies; `Execution context: Sequential same-context — degraded execution` required and downstream `Decision:` / `Verdict:` fields are advisory. The fallback is honest about the loss of isolation, not a workaround that pretends Chat has subagents.
- A single-stage prompt with no downstream consumer (e.g. a Lightweight Pipeline question taken in isolation) — out-of-scope; `None — single-stage prompt with no inter-stage execution mode question` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: /root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md § Phase A1 + § G1 (G1 itself: RULE-P01 governs handoff fields and RULE-P02 governs candidate visibility, but neither addresses execution mode — same-context execution satisfies both rules at the prompt level while collapsing isolation, the gap this rule names).

`Enforced by: Stage 7 self-check sub-check 7e — Execution context: field present on every stage invocation and consistent with the per-target row for the current deployment target. Structural-presence test: tests/test-rule-p03-execution-isolation.sh (verifies the standards document declares Execution context: with the three permitted values, the per-target table, the Stage 7 sub-check 7e linkage, hypothesis marker, and required RULE-001 / RULE-022 / RULE-023 / RULE-031 fields). Per-invocation enforcement of the field at run time is documentation-tier on Claude Chat; mechanical scanning of pipeline-run artifacts for the field is deferred to [PIPELINE-001-7C-LINTER].`

`Deployment-target applicability: Per-target applicability — see the per-target table in this rule's body. The obligation to declare an Execution context: field applies uniformly across deployment targets; the permitted value differs per target (Local + Remote default to Isolated subagent — fresh context; Claude Chat is restricted to Sequential same-context — degraded execution).`

*Self-check: subject `Every pipeline stage invocation` is bare; `Execution context:` permitted values enumerated as three distinct strings (`Isolated subagent — fresh context, INPUT block is the only carried state`, `Sequential same-context — degraded execution, candidates leak across stages`, `None — single-stage prompt with no inter-stage execution mode question`); per-target table present with three deployment-target rows (Claude Code Local, Claude Code Remote, Claude Chat); `Enforced by:` declares Stage 7 sub-check 7e per RULE-023; `Deployment-target applicability:` declares per-target applicability with reference to the in-body table per RULE-031; the authoring run for this rule (`critique-of-pipeline-001-evaluate-modular-shell.md` § Phase A1) executed as an Isolated subagent — fresh context per the Remote row, satisfying the rule on its own authoring artifact.*

### Critique grounding [RULE-P04]

> **Scope:** Process

**Every adversarial-critique artifact must contain a `Verbatim quotes:` line.** Permitted values:
- A list of ≥3 verbatim quotes from the artifact under review, each with a section or line-number reference, *or*
- `None — target is sequestered from this stage's input per RULE-P02 (state which downstream stage receives the target)`.

The line forces the author to confront whether the critique was generated with source contact or from prior assumptions about the target. Zero-quote critiques reinvent constructs the target already contains; the visible `Verbatim quotes:` field converts that failure mode into a surface-checkable shape.

`[Hypothesis: critique-shaped artifacts with zero verbatim quotes from the target were generated without source contact and reinvent constructs the target already contains; disconfirmation = on a 20-critique replay, zero-quote critiques cite source-document constructs at the same rate as ≥3-quote critiques]`.

**Worked example.** A reviewer drafts an external critique of `docs/reference/rule-design-standards.md` recommending mandatory retrieval and provenance checking. The critique header:

```
Target: docs/reference/rule-design-standards.md
Verbatim quotes:
  1. line 107: "None — pipeline output is not a governance artifact"
  2. line 204: "Loop until PASS"
  3. lines 275–278: "Every pipeline INPUT block must contain a `Sequestered:` line"
```

Each quote anchors a claim in the critique body to a precise location in the target. A critique that recommends adding sequestration without quoting line 275 has not read RULE-P02; the missing quote is the signal.

Trigger features: artifact heading or filename containing `critique`, `review`, `assessment`, `evaluation`, or `audit` of a named internal target file or rule (`docs/`, `RULE-NNN`, `[PIPELINE-NNN]`, repository path); or `None — target is unnamed, external, or the critique surface is conversational rather than artifact-shaped`.

Borderline cases:
- A critique of an external paper or pasted text with no file-path reference — out-of-scope; `None — target is unnamed, external, ...` permitted value applies.
- A critique of `docs/reference/rule-design-standards.md` produced by Stage 5 (Adversarial Critique) of `[PIPELINE-001]` where the target is sequestered from this stage's INPUT per RULE-P02 — in-scope but the `None — target is sequestered ...` permitted value applies; the quotes appear at the consuming downstream stage's INPUT block where the target is re-introduced, not in the critique itself.
- A conversational reply containing critique-shaped paragraphs but no artifact header — out-of-scope; the rule fires on artifact production, not conversational turns. Conversational critique that is later promoted into an artifact (filed to a plan, backlog entry, or design document) gains the obligation at promotion.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: /root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md § Phase A3 + § G6 (G6 itself: the pasted critique that motivated this rule contained zero verbatim quotes from `rule-design-standards.md` or `prompt-authoring-background.md`, and its recommendations reinvented Stage 2b / RULE-P02 / RULE-031 — the empirical existence proof for the failure mode this rule names).

`Enforced by: structural-presence test tests/test-rule-p04-critique-grounding.sh (verifies the standards document declares Verbatim quotes: with both permitted values, hypothesis marker, and required RULE-001 / RULE-022 / RULE-023 / RULE-031 fields). Per-critique enforcement of the field at production time is documentation-tier on Claude Chat; mechanical scanning of critique artifacts for the field is deferred to [PIPELINE-001-7C-LINTER].`

`Deployment-target applicability: Applies uniformly across deployment targets (the obligation governs critique-artifact shape, independent of file system / hooks / tests infrastructure availability; the structural-presence test runs on Claude Code Local + Remote where the test suite executes, and is documentation-tier on Claude Chat per RULE-031 / RULE-023 per-target table).`

*Self-check: subject `Every adversarial-critique artifact` is bare; `Verbatim quotes:` permitted values include the `None — target is sequestered ...` form for downstream-handoff cases and the `None — target is unnamed, external, ...` form within the trigger-features block for absent-target cases. The plan that authored this rule (`critique-of-pipeline-001-evaluate-modular-shell.md`) itself contains verbatim quotes from `rule-design-standards.md` — Stage 2b's "None — pipeline output is not a governance artifact" exit at line 107, Stage 7's "Loop until PASS" at line 204, RULE-P02 at lines 275–278 — RULE-P04 satisfied by its own authoring artifact. `Enforced by:` and `Deployment-target applicability:` fields present per RULE-023 / RULE-031.*

### Control Levers

| Lever | How to set it |
|-------|---------------|
| Priorities | State tradeoffs explicitly in Stage 3 `PRIORITIES` block |
| Depth | Add "Concise" or "Rigorous" to TASK instructions |
| Domain hints | Add named domains to Stage 2 TASK if you know them |
| Model tier | Full Pipeline: sonnet (default) or opus when Stage 2 returns ≥5 domains or competing framework tensions. Lightweight Pipeline: haiku or sonnet. **Per-target note:** on Claude Chat, model tier is fixed at session start — mid-pipeline escalation requires session restart with the escalated model. On Claude Code (Local + Remote), the author specifies model tier per stage invocation. See `CLAUDE.md` model tier table and `model-guidance.md` for advisor-session model selection. |

---

## Part 2: Instruction Quality Rules

> See [prompt-authoring-background.md](prompt-authoring-background.md) for the H40 problem and three-tier enforcement model.

**Self-application is a governing principle.** Every rule in this Part applies to its own statement. The format-rule expression of this principle is **RULE-022 (Rule 11)**: every rule section ends with a `Self-check:` line naming which earlier rule applies and the surface feature confirming compliance.

**Stable rule IDs.** Each rule and sub-rule carries a stable `[RULE-NNN]` identifier in its heading (Part 1 structures use `[RULE-P0N]`). IDs are independent of section numbering — they do not change when rules are reordered or renumbered. Prefer ID references (e.g., "per RULE-003") over section-number references (e.g., "per Rule 2") in durable artifacts; section numbers are preserved for backward compatibility only. Conversion table: `rule-id-conversion.md`.

**Mechanism-claim marker default.** Where a rule's body makes a claim about LLM behavior, it carries an inline `[Hypothesis: ...]` marker stating the disconfirmation. Mechanism claims without inline markers inherit the default `[Hypothesis: pipeline-test 2026-05-04 + H40 §18.1 of golem-design.md; disconfirmation = a future pipeline test surfacing the same gaps after these patches land]`.

**Minimum-viable rule expression.** Every field a rule carries must add a non-None permitted value for at least some rules in this guide. Fields whose only valid value for a given rule is `None — <reason>` should be omitted for that rule rather than written out. Do not pad a rule with obligatory `None —` entries. Rule token cost is a compliance factor: every field added is context the model must hold while evaluating the rule.

**Bare-subject requirement scope (retrofit complete v2.3.1).** The transformer-form requirement with bare-noun-phrase subjects (Rule 1) applies as a hard requirement to all rules in this guide. Rules 2–8 (RULE-003 through RULE-013) were retrofitted to bare-subject form in v2.3.1; their Self-check lines now reference the bare-subject + permitted-value pattern. The v2.3.1 synthesis audit reviewed the full rule set for merge candidates (overlapping trigger features and outputs) and split candidates (triggers partitioning into disjoint surface conditions) — **no merges or splits found.** Every rule's `Trigger features:` token set is disjoint from every other rule's, and no rule's permitted-value list partitions into independently-citable sub-rules.

---

### Rule 1: Format rules over self-monitoring [RULE-001] rules

> **Scope:** Authoring

A **format rule** triggers on the act of producing an output. A **self-monitoring rule** triggers on the AI noticing an internal state — and fails under context pressure (H40).

**Format rules come in two shapes: transformer and conditional.** Prefer transformer form.

**Every rule statement must open with one of two phrases:**
- **Transformer (preferred):** `"Every <bare noun phrase> must contain <named element>. Permitted values: <list>, or 'None — <reason>'."` The subject is a single bare noun phrase with no relative clause, no qualifier, no condition modifier. The qualifier (formerly in the subject) moves to the named element's permitted-values list, including a `None — <reason>` entry for the absence case. The rule fires unconditionally on every instance of the bare subject.
- **Conditional (acceptable with justification):** `"When <observable condition>, <required outcome>"`, *and* the rule body must contain a `Surface-feature unavailable:` line stating which surface trigger was searched for and why none could be found.

**Why the bare-subject requirement.** A qualifier in the subject — *"Every plan step **that modifies shared state** must contain..."* — embeds a classification step: the author has to decide whether their plan step modifies shared state before the rule fires. That classification is the H40-vulnerable layer. A bare subject — *"Every plan step must contain a `Propagate to:` bullet (permitted values: target list, or `None — no shared state modified`)"* — fires on every plan step; the qualifier becomes a permitted value, which the author writes as `None — <reason>` when not substantive.

**Authoring test (transformer-vs-conditional):** Read the rule's subject as written. Does it contain a relative clause (`that <verb>`), a participle (`containing <X>`), or a conditional (`when <X>`, `if <X>`)? If yes, the rule is conditional/property-shape; rewrite to bare-subject form, moving the qualifier to a permitted-value clause. If no, the rule is transformer-shaped.

**Authoring test (general):** State the external observable condition that causes the AI to notice the rule applies. If the answer is "the AI should just remember," the rule is self-monitoring. Rewrite it as a format rule, convert it to a skill step or hook, or note explicitly that it is aspirational documentation awaiting structural enforcement.

**Stage specification constraint:** Stage specifications must not contain routing statements of any polarity — neither "Required when X" inside the body nor "Optional for Y" — outside the `Trigger features:` block. Applicability belongs in trigger features, not prose. An "Optional when..." or "Not required for..." sentence in a stage body is a routing decision that removes user agency. `[Hypothesis: embedded optionality statements produce inconsistent scope application; disconfirmation = a corpus check showing consistent scope decisions when routing is embedded in body vs. trigger features.]`

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: this rule complies with itself — its own subject (`Every rule statement`) is a bare noun phrase; the named element (`one of two phrases`) has an explicit permitted-values list (transformer / conditional with justification).*

**Example (canonical transformer form):**
*"Every plan step must contain a `Propagate to:` bullet. Permitted values: list of downstream artifacts to update, or `None — no shared state modified by this step`."*

For contrast pairs (pseudo-transformer and self-monitoring forms) and explanation of why they fail, see [prompt-authoring-background.md §Pedagogical Contrasts](prompt-authoring-background.md#pedagogical-contrasts).

#### 1.1 — Class-of-utterance trigger features [RULE-002]

> **Scope:** Authoring

**Every rule statement must contain a `Trigger features:` field listing the surface tokens that identify an in-scope instance, and a `Borderline cases:` field with ≥2 worked examples.** Permitted values for `Trigger features:` are a comma-separated list of grep-able tokens, *or* `None — applies to all rules of <category>` for meta-rules. Permitted values for `Borderline cases:` are ≥2 worked examples with the trigger features named and the in/out-of-scope call resolved, *or* `None — trigger features apply unambiguously` for rules whose triggers admit no edge cases.

The qualifier formerly in this rule's subject (*"rules whose subject contains a plural quantifier or class noun"*) moves to the `Trigger features:` value: rules without class-of-utterance subjects write `None — applies to all rules of <category>` and the requirement is satisfied trivially.

**Worked example — *"every causal claim needs an epistemic marker."***
- *Trigger features:* the tokens `because`, `caused by`, `due to`, or the arrow `→` in a sentence.
- *Borderline cases:*
  - "X **because** Y" — in-scope; needs a marker.
  - "X is **associated with** Y" — out-of-scope; no marker required (associative, not causal).

**Worked example — *"every quantitative claim needs a source."***
- *Trigger features:* a digit (`0–9`) or a percent token (`%`) in a noun phrase.
- *Borderline cases:*
  - "**3 of 5** runs failed" — in-scope; needs `[Verified: <source>]`.
  - "**most** runs failed" — out-of-scope; flag as Rule 3 vagueness candidate, no source required.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § D1

*Self-check: subject `Every rule statement` is bare; `Trigger features:` and `Borderline cases:` permitted-value lists each include a `None — <reason>` entry for the absence case.*

---

### Rule 2: Format rules first in lists [RULE-003]

> **Scope:** Authoring

**Every authored section must place format rules before all other guidance.** Permitted values: format rules → concrete procedures → principles → examples; or `None — section contains only one type of guidance (no mixed content)`.

When a section mixes format rules with explanatory prose, format rules lose salience if buried after the prose — the same H40-vulnerable displacement that self-monitoring rules suffer at the output level.

Trigger features: section heading in an instruction document where the body contains both a `must`/`Every <bare noun phrase>` statement and explanatory prose, authoring-test paragraphs, or worked examples.

Borderline cases:
- A section with one transformer rule followed only by a worked example — out-of-scope; single rule type present; `None — section contains only one type of guidance` applies.
- A section with a rule statement, then a two-paragraph "Authoring test:" block, then two more rule bullets — in-scope; rule bullets must appear before the Authoring test paragraph.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every authored section` is bare; `None — section contains only one type of guidance (no mixed content)` absorbs the absence case.*

---

### Rule 3: Keep format rules narrow and concrete [RULE-004]

> **Scope:** Authoring

**Every rule statement must be verifiable by reading the artifact alone.** Permitted values: the rule specifies a named surface element (slot, string pattern, count, section header, checkbox transition) that a reader can confirm from the output without a judgment step; or `None — rule is explicitly labeled aspirational documentation, not a format rule`.

A rule that fails this test is either aspirational (label it explicitly) or has a misplaced verification step (move the judgment to a separate inference pass or lower-tier tool).

**Scope qualifiers must be observable.** Replace judgment qualifiers ("non-trivial," "significant," "complex") with observable artifact conditions. Instead of "non-trivial investigation responses," write "responses that include a cause-tree branch, a `[Hypothesis]` tag, or a `Tools used:` footer."

Trigger features: judgment qualifiers in a rule's scope or subject: `non-trivial`, `significant`, `complex`, `important`, `meaningful`, `substantive`, `appropriate`; or any scope clause requiring a judgment step before the rule fires.

Borderline cases:
- *"Start with a one-line hypothesis."* — out-of-scope for Rule 3 (named surface element: `one-line hypothesis` is grep-able and verifiable without judgment). For contrast pairs, see [prompt-authoring-background.md §Pedagogical Contrasts](prompt-authoring-background.md#pedagogical-contrasts).
- *"Apply rigorous investigation to complex failures."* — in-scope; trigger `complex` fires; rewrite: replace `complex` with observable artifact conditions (e.g., "failures with ≥2 implicated components" or "failures where `Tools used:` footer is present").

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every rule statement` is bare; `None — explicitly labeled aspirational documentation, not a format rule` absorbs the absence case.*

---

### Rule 4: Scope rules by behavior, not medium [RULE-005]

> **Scope:** Authoring

**Every rule trigger must name a behavior pattern, not a medium or domain.** Permitted values: a behavior-pattern identifier (observable output characteristic, format element, slot presence, string pattern) that survives the rename test; or `None — rule applies universally across all outputs with no medium restriction`.

**Rename test:** Replace every medium term in the rule with a sibling medium. If the rule still reads sensibly, the trigger is the behavior — scope is correct. If the swap makes it nonsensical, replace the medium name with the behavior trigger.

Trigger features: medium-specific nouns in the rule's scope or trigger clause: `backlog`, `backlog entry`, `response`, `commit message`, `plan`, `plan step`, `PR description`, `comment`, `ticket`, `email`.

Borderline cases:
- *"Commit messages must start with a one-line hypothesis."* — in-scope; trigger `commit messages` fires; rename test: substitute `responses` — rule still reads sensibly — true trigger is `investigation-concluding output`; rewrite to that behavior.
- *"Every causal claim must carry `[Verified]` or `[Hypothesis]`."* — out-of-scope; trigger `causal claim` is a behavior pattern; rename test passes trivially; `None` case applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every rule trigger` is bare; `None — rule applies universally across all outputs with no medium restriction` absorbs the absence case.*

---

### Rule 5: Audit artifact templates for certainty bias [RULE-006]

> **Scope:** Authoring

**Every investigation artifact template must include distinct Observed and Hypotheses slots.** Permitted values: Observed slot (facts each with verification method) + Hypotheses slot (labeled candidates each with cheapest disconfirmation); or `None — template is not an investigation artifact (no cause-diagnosis slots)`.

When all template slots imply certainty (Bug / Cause / Fix), the template gets filled with certainty-shaped prose over hypotheses — the same certainty bias format rules are designed to prevent.

A cause cannot move from *Hypotheses* to *Fix* without first moving into *Observed*.

Trigger features: template specification with ≥2 named slots (bold labels or column headers) where all slots are certainty-shaped: `Bug`, `Cause`, `Fix`, `Root cause`, `Diagnosis`, `Action`, `Resolution` — with no Observed/Hypothesis-shaped slot present.

Borderline cases:
- A template with slots `Bug / Cause / Fix / Priority` for an RCA artifact — in-scope; all four slots are certainty-shaped; trigger fires; `Observed` and `Hypotheses` slots required.
- A template with slots `Title / Description / Owner / Status` for a backlog entry — out-of-scope; no cause-diagnosis slots; `None — template is not an investigation artifact` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every investigation artifact template` is bare; `None — template is not an investigation artifact (no cause-diagnosis slots)` absorbs the absence case.*

#### 5.1 — Quota exit [RULE-007]

> **Scope:** Authoring

**Every rule statement must contain a `Quota exit:` field.** Permitted values:
- *"None at threshold" form* — the literal phrase `"None at threshold"` permitted as a satisfying output value, paired with a one-line justification format, *or*
- *Conditional reformulation* — the rule restated as `"if <surface trigger> then <required output>"` so the rule fires only when the trigger matches, *or*
- `None — no count threshold in this rule`.

`[Hypothesis: quotas without one of the first two forms produce compliance theater — the slot gets filled regardless of evidence; disconfirmation = a quota rule producing artifacts where the Nth item carries evidence-quality comparable to the first]`. This is Rule 5 certainty-bias applied to count slots.

Trigger features: a digit (`0–9`), `≥`, `at least`, `at most`, `exactly`, or `minimum` in a rule's requirement clause — indicating a count threshold or quantity minimum.

Borderline cases:
- *"Every rule must include ≥2 worked examples."* — in-scope; trigger `≥2` fires; `Quota exit:` field required naming the `None at threshold` form or a conditional reformulation.
- *"Every causal claim must carry `[Verified]` or `[Hypothesis]`."* — out-of-scope; no count threshold; `None — no count threshold in this rule` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every rule statement` is bare; `Quota exit:` permitted values include `None — no count threshold` for non-quota rules.*

#### 5.2 — Brevity allowance [RULE-008]

> **Scope:** Authoring

**Every template specification must contain a `Brevity allowance:` field.** Permitted values:
- A list of field names permitted to use the literal form `minimal — <one-line reason>`, *or*
- `None — fewer than 4 required fields` for template specifications below the threshold where padding pressure emerges.

The brevity allowance is the structural escape hatch for field-count requirements (e.g., 7 fields × 7 domains = 49 mandatory cells); without it, thin content gets padded. This is Rule 5.1 applied to template cells rather than list items.

Trigger features: template specification with ≥4 required fields — identified by ≥4 named entries in a `- **<Field>:**` list or table column headers in a rule body.

Borderline cases:
- A template with 7 required fields (`Domain`, `Contribution`, `Weight`, `Interactions`, `Risks`, `Tradeoffs`, `Patterns`) — in-scope; trigger `≥4 required fields` fires; `Brevity allowance:` field required.
- A template with 3 required fields (`Hypothesis`, `Disconfirmation`, `Status`) — out-of-scope; `None — fewer than 4 required fields` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every template specification` is bare; `Brevity allowance:` permitted values include `None — fewer than 4 required fields` for templates below the threshold.*

---

### Rule 6: Test new rules behaviorally, not just by reading [RULE-009]

> **Scope:** Authoring

**Every new rule addition must include an observable behavioral test condition.** Permitted values: a falsifiable condition demonstrating the rule prevents the failure it addresses (e.g., `sessions in which behavior X previously occurred no longer produce behavior X under conditions Y`); or `None — rule governs structural form only, with no behavioral outcome to test`.

A rule that reads well but fails in practice has a salience, trigger, or scope problem. Text review does not catch these.

**Authoring test:** When adding a rule that addresses a recurring failure, state the observable condition demonstrating the rule is working. If that condition cannot be stated, the rule is not falsifiable.

Trigger features: a new `### Rule N:` or `#### N.M —` heading being added to an instruction document; or a new behavioral obligation row in a CLAUDE.md or SKILL.md table containing `prevents`, `eliminates`, `ensures`, or `causes the AI to`.

Borderline cases:
- Adding a rule that eliminates a known H40 pattern in causal-claim emission — in-scope; trigger `new rule heading` fires; falsifiable condition required.
- Revising the wording of an existing rule without changing its behavioral scope — out-of-scope; no new rule being added; Rule 7 (retrofit audit) applies instead.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every new rule addition` is bare; `None — rule governs structural form only, with no behavioral outcome to test` absorbs the absence case.*

#### 6.1 — Falsifiability tokens [RULE-010]

> **Scope:** Authoring

**Every rule statement must contain a `Falsifiability:` field.** Permitted values:
- All three of `threshold: <digit | comparator | rate phrase>; horizon: <time-bound | count-bound>; role: <named evaluator>`, *or*
- `None — descriptive guidance, not falsifiable behavioral claim` for rules whose subject describes structural form rather than asserting a behavioral outcome.

A `Falsifiability:` value missing any of the three sub-tokens reads as falsifiable but cannot be tested. *"X no longer happens"* fails all three — no threshold, no horizon, no evaluator.

Trigger features: behavioral-outcome verbs in a rule body: `prevents`, `eliminates`, `ensures`, `causes`, `produces`, `results in`, `changes`, `stops`, `reduces`, `addresses a recurring failure` — indicating a behavioral claim that must be testable.

Borderline cases:
- *"Rule X prevents H40 violations in causal-claim emission."* — in-scope; trigger `prevents` fires; `Falsifiability:` with threshold + horizon + role required.
- *"Every rule statement ends with a `Self-check:` line."* — out-of-scope; body asserts structural form, not behavioral outcome; `None — descriptive guidance, not falsifiable behavioral claim` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every rule statement` is bare; `Falsifiability:` permitted values include `None — descriptive guidance` for non-behavioral rules.*

---

### Rule 7: Audit current artifacts when adding a new rule [RULE-011]

> **Scope:** Authoring

**Every new rule promotion to operational status must be preceded by a compliance scan of in-scope artifacts.** Permitted values: a documented scan covering introductory and framing prose (not only named rule statements) plus a disposition for each non-compliant artifact (fixed in session, or backlog item with ID); or `None — rule fires only on artifacts created after this commit (no pre-existing in-scope artifacts)`.

Adding a rule prevents future violations; it does not fix existing ones.

**Before marking any new rule operational:**
1. Identify the in-scope artifacts (behavior-scoped set per Rule 4).
2. Re-scan for compliance — including introductory and framing prose within sections, not only named rule statements and table rows.
3. Fix non-compliant artifacts in the same session, or create a backlog item for the retrofit.

Trigger features: plan verification checkbox `- [x]` on a rule-addition item; `git commit` on a file with a newly-added `### Rule N:` or `[RULE-NNN]` heading; plan ceremony step closing a rule-delivery package.

Borderline cases:
- Marking Rule 7.1 (Applicability) operational in a plan — in-scope; trigger fires; scan all in-scope instruction documents for missing `Applicability:` fields, fix or backlog.
- Adding a new backlog item proposing a future rule — out-of-scope; no rule being marked operational; scan deferred until the rule is implemented.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

Deployment-target applicability: Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | Full file scan of in-scope artifacts (CLAUDE.md, SKILL.md files, plan files); fix in session or backlog item per the standard procedure |
| Claude Chat | `Not enforceable on this deployment target — manual author responsibility (compliance scan limited to material accessible in conversation context: pasted text, uploaded documents, prior turns)` |

*Self-check: subject `Every new rule promotion to operational status` is bare; `None — rule fires only on artifacts created after this commit (no pre-existing in-scope artifacts)` absorbs the absence case; `Deployment-target applicability:` per-target table present (RULE-031 satisfied — rule body cites in-scope artifacts and the standard backlog item form, both infrastructure tokens).*

#### 7.1 — Applicability [RULE-012]

> **Scope:** Authoring

**Every rule statement must contain an `Applicability:` field.** Permitted values:
- The literal phrase **`Applies in all contexts`** (no override permitted), *or*
- `Override: <mechanism>; bookkeeping: <required artifact>` naming a specific bypass mechanism (a flag, an environment variable, a session-marker file) and what gets recorded when used (e.g., *`Override: --dev-iteration flag; bookkeeping: session log entry with timestamp + reason`*), *or*
- `None — not a procedural-constraint rule` for rules whose body contains no imperative halt/block/wait/must-not/refuse/stop verbs.

A procedural-constraint rule with no `Applies in all contexts` and no `Override:` (other than `None`) creates a hidden choice between violating the rule (to iterate) and following it (and being unable to test); the author defaults to violation. Rules constraining rule-authoring workflow are the highest-risk class.

Trigger features: procedural-constraint verbs in a rule body: `halt`, `block`, `wait`, `must not`, `refuse`, `stop`, `pause`, `cannot`, `forbidden`, `prohibited` — indicating a procedural constraint that may need a development-context override.

Borderline cases:
- *"An agent must not read files outside the worktree boundary."* — in-scope; trigger `must not` fires; `Applicability:` with `Applies in all contexts` or `Override: <mechanism>` required.
- *"Every rule statement ends with a `Self-check:` line."* — out-of-scope; no procedural-constraint verb; `None — not a procedural-constraint rule` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every rule statement` is bare; `Applicability:` permitted values include `None — not a procedural-constraint rule` for non-procedural rules.*

---

> **Scope boundary.** RULE-001 through RULE-012, RULE-020 through RULE-026 are **authoring-scope**: they govern the shape and structure of rule statements and instruction documents. RULE-013 through RULE-019 below are **output-scope**: they govern investigation-concluding outputs that Claude produces, not how rules are written. Both sets are listed in Part 2 because they share the same format-rule/self-check conventions, but their application contexts differ.

---

### Rule 8: Investigation-concluding outputs require epistemic markers [RULE-013]

> **Scope:** Output

**Every investigation-concluding output must carry epistemic markers at each causal claim.** Permitted values: `[Verified: source]` or `[Hypothesis: cheapest observation that would confirm or falsify]` at each causal claim; or `None — output is a retrospective reflection (labeled `Single-loop:` / `Double-loop:` / `Triple-loop:`) or brainstorming response with no causal claim`.

If a reader could act on the output assuming the cause is confirmed, Rule 8 applies — sub-clauses 8.1–8.6 below specify the required marker forms.

Trigger features: causal tokens `because`, `caused by`, `due to`, `→`, `therefore`, `led to`, `resulted in`; diagnostic section headers `Root cause:`, `Finding:`, `Diagnosis:`, `Cause:`; absence claim phrases `not found`, `unavailable`, `not documented`, `out of scope`.

Borderline cases:
- *"The deploy failed because the cache wasn't cleared."* — in-scope; trigger `because` fires; `[Hypothesis: cache wasn't cleared — disconfirmation: re-run with cache clear]` required.
- *"Single-loop: I followed the plan steps."* — out-of-scope; `Single-loop:` label fires the `None` permitted value (retrospective reflection, no causal claim about an external system).

#### 8.1 — Hypothesis preamble (format) [RULE-014]

> **Scope:** Output

The first two lines of any response containing a `[Hypothesis:]` tag, cause-tree branch, or `Tools used:` footer must state:

```
(a) one-line hypothesis
(b) cheapest thing that would disconfirm it
```

If genuinely unknown: *"Hypothesis: I don't have enough information. Cheapest disconfirmation: ask the user what they are seeing."*

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

#### 8.2 — Inline claim tags (format) [RULE-015]

> **Scope:** Output

Any claim about why a system behaves as it does, how a component works, or what is "documented," "expected," or "by design" must carry an inline tag:
- `[Verified: source]` — URL, file:line, command output, or log quote
- `[Hypothesis: cheapest observation that would confirm or falsify]`

Language such as "documented behavior" or "as expected" without an inline tag is malformed output.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

#### 8.3 — Per-component defect hypothesis (format) [RULE-016]

> **Scope:** Output

Any hypothesis list must include at least one "this component has a defect" hypothesis per component in the causal chain. Trusted components (platform, runtime, language, own code) do not receive implicit correctness.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

#### 8.4 — Tools used: footer (format) [RULE-017]

> **Scope:** Output

Any output asserting a cause, diagnosis, or "root cause found"-grade conclusion must end with:

```
Tools used: [list of investigative steps taken]. [For any natural-candidate tool not used: state why in one phrase.]
```

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

#### 8.5 — Absence enumeration (format) [RULE-018]

> **Scope:** Output

Before any report of "not found," "unavailable," "not documented," or "out of scope," inline-list the investigative tools used and what each returned. Absence reported without that enumeration is malformed output.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

#### 8.6 — Evidence scope (format) [RULE-019]

> **Scope:** Output

Any claim generalizing from a single probe to a system must explicitly state: *"This confirms [one probe], not the system it belongs to."*

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original sub-rules of Rule 8)

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v1.0.0 (original rule set)

*Self-check: subject `Every investigation-concluding output` is bare; `None — retrospective reflection or brainstorming with no causal claim` absorbs the absence case. Sub-clauses 8.1–8.6 specify per-marker form for each causal-claim surface token.*

---

### Rule 9: Procedural form [RULE-020]

> **Scope:** Authoring

**Every rule statement must contain a `Procedural form:` field.** Permitted values:
- All three of `Trigger: <surface condition>; Steps: <ordered sequence>; Output: <discrete artifact>` — where Trigger names a token pattern, section header, checkbox transition, or tool-call result; each Step's completion is confirmable from output; Output is a revised artifact, a `Stipulation:` line, or a recorded log entry, *or*
- `None — not a procedural command (no halt/reconsider/audit/review/verify/reflect/check imperative)`.

Procedural commands lacking the three blocks read behavioral ("the AI does X") but trigger on internal states ("when X seems necessary") — Rule 1 violations in clothing.

**Worked example (canonical operational form):**
- *Trigger:* `[Verified]` count = 0 in a causal-claim section.
- *Steps:* (1) re-check the claim's surface tokens; (2) attempt to produce a `[Verified: <source>]` marker; (3) if none available, write a `Stipulation:` line.
- *Output:* either revised output with ≥1 `[Verified: <source>]` marker, or a `Stipulation: <reason>` line.

For aspirational/weak procedural-command examples and explanation of why they fail, see [prompt-authoring-background.md §Pedagogical Contrasts](prompt-authoring-background.md#pedagogical-contrasts).

Trigger features: procedural-command verbs in a rule body: `halt`, `reconsider`, `audit`, `review`, `verify`, `reflect`, `check`, `pause`, `re-examine`, `confirm`, `validate` — indicating an imperative that must terminate in a discrete artifact.

Borderline cases:
- *"On every causal claim, halt and verify the marker is present."* — in-scope; triggers `halt` + `verify` fire; `Procedural form:` field required naming Trigger / Steps / Output.
- *"Causal claims carry `[Verified]` or `[Hypothesis]` markers."* — out-of-scope; no procedural-command verb; the `None — not a procedural command` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every rule statement` is bare; `Procedural form:` permitted values include `None — not a procedural command` for non-procedural rules.*

---

### Rule 10: Pipeline applicability [RULE-021]

> **Scope:** Authoring

**Every rule statement must contain a `Pipeline applicability:` field.** Permitted values:
- The literal phrase **`Applies uniformly across stages`**, *or*
- `Per-stage applicability: <table or list>` naming each stage the rule applies to and how it differs at each, *or*
- `None — not pipeline-spanning (no stage / pipeline / Stage N tokens in this rule's body)`.

A pipeline-spanning rule lacking the field's first two values produces stage-inappropriate compliance — a rule designed for a synthesis stage misfires at a framing stage where its preconditions don't hold.

**Worked example.** *"Every causal claim needs a `[Verified: source]` marker."* — cannot apply uniformly because at Stage 1 (Framing) no verification has happened yet. Per-stage form:
- *Pipeline applicability: Per-stage applicability:*
  - **Stages 1–3 (Framing, Routing, Analysis):** `[Hypothesis: <claim> — disconfirmation: <observation>]` only; `[Verified]` not yet available.
  - **Stages 4–6 (Synthesis, Critique, Refinement):** `[Verified: <source>]` required for any causal claim; `[Hypothesis]` permitted for unresolved candidates.

Trigger features: stage references in a rule body — the tokens `Stage <N>`, `Stage N`, `pipeline`, `across stages`; or numbered stage names (`Framing`, `Routing`, `Analysis`, `Synthesis`, `Critique`, `Refinement`).

Borderline cases:
- *"Every causal claim needs a `[Verified: source]` marker."* applied across the 6-stage pipeline — in-scope; trigger fires at Stage 1 (Framing) where verification is impossible; `Per-stage applicability:` table required.
- *"Every rule statement ends with a `Self-check:` line."* — out-of-scope; rule body contains no pipeline-stage tokens; the `None — not pipeline-spanning` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-pipeline-feedback.md § v2.1.0 patches

*Self-check: subject `Every rule statement` is bare; `Pipeline applicability:` permitted values include `None — not pipeline-spanning` for non-pipeline rules.*

---

### Rule 11: Self-check [RULE-022]

> **Scope:** Authoring

**Every rule statement must end with a `Self-check:` line.** Permitted values:
- `<bare-subject confirmation>; <permitted-value list reference>` — confirming the rule's own subject is bare-noun-phrase form and naming the field's permitted-value clause that absorbs the absence case, *or*
- `None — meta-rule (Part 2 preamble; this rule itself, Rule 11)` for the principle's root statement.

A rule lacking a `Self-check:` line is self-exempting: the author has implicitly classified the rule as too important to govern its own author — the same psychological mechanism that produces the violations the rule was written to prevent.

This rule is the meta-clause of Part 2 (named in the preamble above). Numbered Rule 11 for cite stability — see the changelog entry for v2.1.0 — but the principle governs every rule.

Trigger features: `### Rule`, `#### <N.M>`, `[RULE-NNN]` or `[RULE-P0N]` heading anchors; the literal phrase `Every rule statement` or `Every <bare noun phrase> must`; any rule-like obligation in CLAUDE.md or SKILL.md with a `must contain` structure.

Borderline cases:
- A new sub-rule `#### 5.3 — Token budget [RULE-NNN]` with body and permitted-value list — in-scope; trigger `#### <N.M>` fires; `Self-check:` line required confirming bare-subject form and permitted-value clause.
- The Part 2 preamble paragraph "Self-application is a governing principle" — out-of-scope; the `None — meta-rule (Part 2 preamble; this rule itself, Rule 11)` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/reference/rule-design-standards.md v2.2.0 (Self-check addition)

*Self-check: subject `Every rule statement` is bare; `Self-check:` permitted values include `None — meta-rule` for the principle's root statement.*

---

### Rule 12: Enforcement location for unconditional obligations [RULE-023]

> **Scope:** Authoring

**Every unconditional behavioral obligation must contain an `Enforced by:` field naming the structural gate that fires it.** Permitted values:
- A named procedural anchor located in the same artifact — `Enforced by: <step N of <named procedure> | checkbox in <section> | Trigger/Steps/Output block at <heading>>` whose firing is confirmable from output, *or*
- A named structural enforcement outside the procedural sequence — `Enforced by: hook <hook name in .claude/settings.json>` or `Enforced by: test <tests/test-*.sh>` naming the file whose execution gates the obligation, *or*
- The literal phrase `Enforced by: Documentation-tier only — backlog: <backlog item ID>` paired with a dated backlog entry, opting out of structural enforcement with tracked retrofit, *or*
- `None — no unconditional-obligation token in this rule's body`.

A behavioral obligation stated in definitional prose without an `Enforced by:` anchor decouples the requirement from the structural sequence that enforces it; runtime salience competition (H40) then bypasses the unenforced obligation. This rule fires on the prose surface — the obligation's own author writes the gate citation — eliminating the cross-section reading step that produced regression `step4-bypass-L3-001` (walkthrough RCA 2026-05-03).

**Distinction from Rule 9 (RULE-020).** Rule 9 governs procedural commands needing operational definitions *inside* a single rule statement (imperative verbs `halt|reconsider|audit|review|verify|reflect|check`). Rule 12 governs unconditional-obligation prose *across* sections — the gate may live in a different section, file, hook, or test. The trigger sets are disjoint; co-firing on a rule body containing both an imperative verb and an unconditional-obligation token is permitted.

**Authoring test:** Grep the rule body for the trigger tokens listed below. If any fires, locate the `Enforced by:` line in the same rule body. If absent, add the line naming the gate, or use a None-case permitted value.

`[Hypothesis: unconditional-obligation prose without an \`Enforced by:\` anchor produces runtime gate-bypass at a rate comparable to triggerless rules; disconfirmation = a corpus of obligation-prose entries with anchors and a control set without anchors showing equivalent bypass rates under context-pressure runs]`.

Trigger features: `unconditionally`, `fires unconditionally`, `Fires unconditionally`, `always fires`, `without exception`, `regardless of context`, `for every <noun>` paired with `must` in a definitional (non-procedural-step-list) section.

Borderline cases:
- *"`/idp-rca --feedback <n>` fires unconditionally for every ERROR row."* — in-scope; trigger `fires unconditionally` fires; the obligation already names the enforcing skill invocation inline, which constitutes the `Enforced by:` anchor; rule satisfied if that invocation is written as `Enforced by: /idp-rca --feedback skill invocation`.
- *"Every causal claim ends with one of the two markers."* (Part 3 catch-all) — in-scope; `Every <noun>` + `must` pattern present in a definitional section; `Enforced by:` field required naming the lint test (e.g., `Enforced by: tests/test-rule-design-compliance.sh causal-claim assertion`).
- *"Format rules trigger on the act of producing an output."* (Rule 1 prose) — out-of-scope; no unconditional-obligation token in the sentence; `None — no unconditional-obligation token in this rule's body` permitted value applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-coherence-rework.md § Package C

Deployment-target applicability: Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | All four permitted values available — `Enforced by: <step N of <named procedure>>`, `Enforced by: hook <hook name>`, `Enforced by: test <tests/test-*.sh>`, or `Enforced by: Documentation-tier only — backlog: <ID>` |
| Claude Chat | Only `Enforced by: Not enforceable on this deployment target — manual author responsibility` permitted (the named-tier values reference hook / test / backlog infrastructure that does not exist on this deployment target) |

*Self-check: subject `Every unconditional behavioral obligation` is bare; `Enforced by:` permitted values include `None — no unconditional-obligation token in this rule's body` for the absence case; `Deployment-target applicability:` per-target table present (RULE-031 satisfied — rule body cites hook / test / backlog infrastructure).*

---

### Rule 13: Trigger vocabulary disambiguation [RULE-024]

> **Scope:** Authoring

**Every step in a multi-step instruction document must contain a `Closed synonym list:` field, and exactly one step in each collision pair must contain a `Precedence:` field.** Permitted values for `Closed synonym list:`:
- A comma-separated list of terms followed by the literal closure assertion `No other terms resolve to this step.`, *or*
- `None — this step has no synonym overlap with other steps in this document`, *or*
- `None — steps are gated by document-phase precondition (this step can only fire after Step <M> completes)`, *or*
- `None — document contains fewer than 2 steps with trigger-bearing bodies`.

Permitted values for `Precedence:`:
- `Precedence: Step <N> over Step <M> when <observable token, position, or surface shape in the user message>` — the condition must be a literal token, the user message's position relative to a prior prompt, or a structural shape in the user message; the words `intent`, `context`, `purpose`, `meaning` are not permitted as the condition, *or*
- `None — no collision pair exists in this document` (paired with the corresponding `Closed synonym list:` None form).

A multi-step skill where ≥2 steps share trigger vocabulary without a closed list and a precedence rule routes the user message to the nearest output-shape step rather than the upstream routing step (the T5.29 regression class). Closed synonym lists alone do not resolve overlap — a precedence rule is required when lists intersect.

**Worked example — walkthrough Step 4a (Route) vs. Step 5 (Plan Sign-off).** Both steps can fire on a "yes/go ahead" user response.
- *Step 4a trigger:* user-message tokens `route`, `confirm routing`, `confirm`, `yes`. *Closed synonym list:* `route, confirm routing, confirm, yes (when emitted in response to a routing-table prompt)`. *No other terms resolve to this step.*
- *Step 5 trigger:* user-message tokens `accept`, `accepted`, `approve`, `sign off`. *Closed synonym list:* `accept, accepted, approve, approved, sign off, signed off`. *No other terms resolve to this step.*
- *Precedence:* Step 4a over Step 5 when the user message immediately follows a routing-table prompt (the prior assistant message contains the literal token `Reply with row overrides` or `confirm routing`). Otherwise Step 5 fires.

Trigger features: ≥2 headings matching `### Step N` or `#### Step N.M` in the same document body AND ≥2 of those step bodies contain at least one of the literal tokens `Trigger:`, `Triggers:`, `Synonyms:`, `Fires on:`, `Closed synonym list:`, or a comma-separated user-phrase list under a heading containing `accept`, `confirm`, `route`, or `proceed`.

Borderline cases:
- Walkthrough SKILL.md Step 3.5 Synonym gate names `implement`, `accept`, `proceed`, `yes`, `go ahead` and states precedence over Step 4a — in-scope; ≥2 step headings present; trigger-bearing bodies present; `Closed synonym list:` and `Precedence:` fields required per this rule.
- A two-step skill where Step 1 fires on `start` and Step 2 fires on `summarize` — out-of-scope; vocabularies disjoint; both steps carry `Closed synonym list: None — this step has no synonym overlap with other steps in this document`.
- A skill with one step plus several non-step procedural sections — out-of-scope; fewer than 2 step headings; `Closed synonym list: None — document contains fewer than 2 steps with trigger-bearing bodies` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-coherence-rework.md § Package D

*Self-check: subject `Every step in a multi-step instruction document` is bare; `Closed synonym list:` permitted values include three `None — <reason>` entries (no overlap, phase-gated, fewer than 2 steps); `Precedence:` permitted values include `None — no collision pair exists` for the absence case.*

---

### Rule 14: Pipeline-bypass detection [RULE-025]

> **Scope:** Authoring

**Every section heading containing a stable-ID token must contain a `Pipeline evidence:` field in its body.** Permitted values:
- A relative file path to a committed plan or pipeline-transcript file paired with a section name (form: `Pipeline evidence: <path> § <section>`), *or*
- The literal phrase `Pipeline evidence: lightweight variant — <one-line reason>` paired with the five-question Lightweight Pipeline answers recorded in the section body, *or*
- The literal phrase `Pipeline evidence: Claude Chat session — <date or topic>` paired with conversation context for surfaces that lack a committed file system (Claude Chat), *or*
- `Pipeline evidence: None — cross-reference heading; original pipeline at <stable-ID>` where `<stable-ID>` resolves to another section in the corpus with its own `Pipeline evidence:` citation, *or*
- `None — heading does not contain a stable-ID token`.

**Authoring test (full-pipeline misclassification on Claude Chat).** If you ran 6+ stages, you ran the Full Pipeline (`[PIPELINE-001]`); do not select the lightweight permitted value to satisfy this gate. Use the Claude Chat session form when the file path form is unavailable on your surface.

A pipeline-bypass detection rule fires on the surface marker that distinguishes a rule introduction from prose: the heading-co-located stable-ID token. Prose cross-references to existing rules (e.g., a CLAUDE.md sentence "per RULE-009") do not carry headings and do not fire this rule.

`[Hypothesis: instruction-document additions with stable-ID tokens but no Pipeline evidence field reach commit at a rate ≥ 1 per 10 rule-promotion sessions; disconfirmation = a rolling 10-session window after RULE-025 lands showing that rate at or below zero]`.

**Coverage limitation.** Non-ID-bearing additions to instruction documents (new Conventions-table entries, new banned-phrase rows in Part 3 of this guide, new template fields inside an existing rule body) are out of trigger for RULE-025.

Trigger features: a heading line (`#` through `####`) in an instruction document containing one of the bracketed tokens `[RULE-`, `[RULE-P0`, `[T5.`, `[ERR-`, `[PA-`, `[ANT-`, `[EXP-`, `[PIPELINE-`.

Borderline cases:
- A new heading `### Rule 15: First-time-reader gate [RULE-026]` in `rule-design-standards.md` — in-scope; trigger `[RULE-` fires; `Pipeline evidence:` field required naming the pipeline plan path.
- A CLAUDE.md sentence "the audit step in RULE-011 covers this" — out-of-scope; no heading present; trigger does not fire.
- A heading `### Conversion entry [RULE-025]` in `rule-id-conversion.md` whose body is a single table row — in-scope; trigger fires; `Pipeline evidence: None — cross-reference heading; original pipeline at RULE-025` permitted value applies.
- A heading `### [PIPELINE-002] Lightweight Pipeline` in `rule-design-standards.md` — in-scope; trigger `[PIPELINE-` fires; `Pipeline evidence:` field required (the Pipeline Registry preamble plus the original pipeline definition's pipeline plan satisfy this).

Prerequisites: RULE-001, RULE-002, RULE-004, RULE-022.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-coherence-rework.md § Package E.

Deployment-target applicability: Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | File-path citation form (`<path> § <section>`) preferred; lightweight and cross-reference forms also available |
| Claude Chat | `Pipeline evidence: Claude Chat session — <date or topic>` form is canonical (file-path form is structurally unavailable on this deployment target; lightweight form is reserved for `[PIPELINE-002]` runs only) |

*Self-check: subject `Every section heading containing a stable-ID token` is bare; `Pipeline evidence:` permitted values include `None — heading does not contain a stable-ID token` for the absence case, `Pipeline evidence: None — cross-reference heading; original pipeline at <stable-ID>` for the cross-reference case, and `Pipeline evidence: Claude Chat session — <date or topic>` for the deployment target where file paths are unavailable; `Deployment-target applicability:` per-target table present (RULE-031 satisfied — rule body cites `docs/plans/` paths, an infrastructure token).*

---

### Rule 15: First-time-reader gate [RULE-026]

> **Scope:** Authoring

**Every section heading containing a stable-ID token must contain a `Prerequisites:` field and a `Changes summary:` field in its body.** Permitted values for `Prerequisites:`:
- A comma-separated list of stable-ID tokens (`RULE-NNN`, `RULE-P0N`, `T5.NN`, `ERR-NNN`) naming the rules or conventions the section depends on, *or*
- `None — section body contains no dependency surface markers (\`per RULE-\`, \`see RULE-\`, \`requires\`, \`depends on\`)`, *or*
- `None — heading does not contain a stable-ID token`.

Permitted values for `Changes summary:`:
- A bulleted list `- <stable-ID or section>: <one-line change description>` for each prior rule or section the present section modifies, *or*
- `None — section body contains no modification surface markers (\`supersedes\`, \`replaces\`, \`rewrites\`, \`modifies\`, \`deprecates\`, \`now reads\`)`, *or*
- `None — heading does not contain a stable-ID token`.

A first-time-reader gate fires on the same trigger surface as RULE-025. The two fields make the section's dependency and modification footprint surface-verifiable without requiring a diff tool.

Trigger features: identical to RULE-025 — a heading line (`#` through `####`) in an instruction document containing one of the bracketed tokens `[RULE-`, `[RULE-P0`, `[T5.`, `[ERR-`, `[PA-`, `[ANT-`, `[EXP-`, `[PIPELINE-`.

Borderline cases:
- A new heading `### Rule 14: Pipeline-bypass detection [RULE-025]` whose body cites RULE-001, RULE-002, RULE-004, RULE-022 — in-scope; trigger fires; `Prerequisites: RULE-001, RULE-002, RULE-004, RULE-022` required. Body contains no modification markers; `Changes summary: None — section body contains no modification surface markers` applies.
- A heading `### Rule 1: Format rules... [RULE-001]` (existing, pre-RULE-026) — in-scope retrospectively; RULE-011 (Rule 7) retroactive audit applies; both fields added as None forms during retrofit (backlog: T5.35).
- A CLAUDE.md prose paragraph referencing RULE-009 — out-of-scope; no heading present; trigger does not fire.

Prerequisites: RULE-025.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/rule-design-standards-coherence-rework.md § Package E.

*Self-check: subject `Every section heading containing a stable-ID token` is bare; `Prerequisites:` permitted values include `None — section body contains no dependency surface markers` and `None — heading does not contain a stable-ID token` for absence cases; `Changes summary:` permitted values include `None — section body contains no modification surface markers` and `None — heading does not contain a stable-ID token` for absence cases.*

---

### Rule 16: Stage 7 obligation [RULE-028]

> **Scope:** Process

**Every full pipeline execution must include a Stage 7 Whole-Output Coherence Review before marking the output IMPLEMENTED.** Permitted values for the Stage 7 record:
- `Stage 7 verdict: PASS` — all four checks clear; output is coherent
- `Stage 7 verdict: CORRECTED — <list of corrections applied>` — issues found; returned to Stage 6 for corrections; re-ran Stage 7; now PASS
- `Stage 7 verdict: BLOCKED — <issue>` — contradiction or broken citation found; returned to Stage 6; re-ran Stage 7 after resolution; now PASS
- `Stage 7 verdict: PRIMARY+DISSENT — <primary position> // <dissent position>` — Stage 7 and Stage 6 stably disagree; both positions recorded in verification log; artifact proceeds to IMPLEMENTED with the dissent signal preserved for downstream reviewers. See Stage 7 § Termination
- `Stage 7 verdict: ESCALATED — <full check trace>` — degenerate exit (Stage 7 cannot produce any verdict — e.g., self-referential contradiction, infrastructure unavailable); halted for human review. Permitted as final state only with a `Human-review override:` note in the plan verification log naming the reviewer and rationale; otherwise IMPLEMENTED is blocked
- `None — lightweight pipeline variant; output is ephemeral (not committed, not shared externally, not acted on without further review)`

A Stage 7 record must appear in the commit message, the plan's verification section, or the output artifact itself. Absence of a Stage 7 record on a committed durable artifact is a RULE-028 violation.

Trigger features: any pipeline execution producing a committed artifact (rule set, guide, plan, standard, instruction template); or `None — pipeline output is ephemeral`.

Borderline cases:
- A session-end `/test local` run producing a passing test suite but no committed rule changes — out-of-scope; no durable governance artifact produced; `None —` permitted value applies.
- A walkthrough pass that adds three new rules to `rule-design-standards.md` and marks IMPLEMENTED without a Stage 7 run — in-scope; trigger fires; Stage 7 required before IMPLEMENTED.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/ — RCA feedback row 6, walkthrough on a deployment branch of the source project (2026-05-05).

`Enforced by: plan completion ceremony self-compliance gate (CLAUDE.md) + walkthrough Step 4a routing table Stage 7 check.`

Deployment-target applicability: Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | All four sub-checks (7a–7d) executable; cross-reference completeness (7c) verifies referenced files exist via file system access |
| Claude Chat | Sub-checks 7a (section order), 7b (internal consistency), 7d (document-type fit) executable from output alone. Sub-check 7c is limited to material accessible in conversation context (uploaded documents, prior turns); referenced repository file paths cannot be verified — author records `[7c limited: file paths unverifiable on this deployment target]` alongside the verdict |

*Self-check: subject `Every full pipeline execution` is bare; permitted values include `None — lightweight pipeline, output is ephemeral` for the non-triggering case; `Enforced by:` field is present (RULE-023 satisfied); `Deployment-target applicability:` per-target table present (RULE-031 satisfied — rule body cites hook / test / commit-message infrastructure plus cross-reference verification).*

---

### Rule 17: Scope classification decision procedure [RULE-029]

> **Scope:** Authoring

**Every rule scope declaration must be assigned using the three-question decision procedure.** Permitted values for scope:
- `Authoring` — Q1 answers Yes: the rule fires at authoring time on an instruction artifact
- `Output` — Q1 answers No, Q2 answers Yes: the rule governs tokens emitted in a response
- `Process` — Q1 and Q2 answer No, Q3 answers Yes: the rule governs pipeline stage boundary behavior
- `None — rule section heading does not contain a stable-ID token (scope declaration not required)`

**Three-question decision procedure:**
- **Q1:** Does the rule fire when an author is writing or editing an instruction artifact (CLAUDE.md, SKILL.md, rule section, plan template, error catalog entry, experiment contract)? If yes → **Authoring**.
- **Q2:** Does the rule govern the shape or content of tokens an AI emits in a response (format of investigation outputs, required fields in analysis artifacts, banned phrases in causal claims)? If yes → **Output**.
- **Q3:** Does the rule govern what passes between pipeline stages, how stages are sequenced, or what a stage boundary must contain (cross-stage handoff fields, sequestration lines, stage-spanning rules)? If yes → **Process**.

If none of the three questions answers Yes, the rule does not belong in this guide — verify scope before promotion.

Trigger features: any rule section in Part 2 carrying a `> **Scope:**` declaration; or `None — section has no scope declaration`.

Borderline cases:
- RULE-013 (epistemic markers on investigation outputs) — Q1: fires when an author writes an investigation-concluding output — Yes. Q1 could classify it as Authoring; but the trigger is the tokens the AI emits (investigation-concluding output format), not the authoring act on an instruction artifact. Q2 is more specific: governs tokens emitted. Scope = **Output**.
- RULE-P01 (cross-stage handoff structure) — Q1: fires when authoring a stage output specification — Yes. But the stage output specification governs pipeline boundary behavior (what passes between stages). Q3 is more specific. Scope = **Process**.
- RULE-001 (format rules over self-monitoring) — Q1: fires when an author writes a rule statement — Yes. Scope = **Authoring**. Q2 and Q3 do not apply: the rule governs the shape of rule statements, not response tokens or stage boundaries.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/ — RCA feedback row 7, walkthrough on a deployment branch of the source project (2026-05-05).

*Self-check: subject `Every rule scope declaration` is bare; permitted values enumerate all four outcomes including `None —` for the no-stable-ID case; three-question procedure is self-applying — this rule's own scope: Q1 fires when an author writes a scope declaration (authoring act on instruction artifact) → Authoring.*

---

### Rule 18: Prior art evidence for governance artifacts [RULE-030]

> **Scope:** Process

**Every pipeline execution producing a governance artifact (guide, rule set, standard, instruction template) must include a Stage 2b (Prior Art & Convergence Check) output before Stage 3.** Permitted values for the Stage 2b record:
- A `Stage 2b artifact:` field in the plan or commit message citing the prior art search output (convergence map + simplification candidates + gaps)
- `None — pipeline output is not a governance artifact`
- `None — prior art search was completed within the past 90 days for this artifact (cite date and source)`

The Stage 2b output must include the convergence percentage. If ≥70% of proposed rules map onto an existing external taxonomy, the decision to redesign from the taxonomy (rather than append) must be documented before proceeding to Stage 3.

Trigger features: a pipeline run where Stage 1 output classifies the task as producing a guide, rule set, standard, or instruction template; or `None — pipeline output is not a governance artifact`.

Borderline cases:
- A pipeline producing a new rule for `rule-design-standards.md` — in-scope; governance artifact modified; Stage 2b required; prior art for the rule type must be documented.
- A pipeline producing a strategic analysis report (`/report`) — out-of-scope; report is an analysis output, not a governance artifact; `None — pipeline output is not a governance artifact` applies.

Prerequisites: None — section body contains no dependency surface markers.

Changes summary: None — section body contains no modification surface markers.

Pipeline evidence: docs/plans/ — RCA feedback row 8, walkthrough on a deployment branch of the source project (2026-05-05).

`Enforced by: Stage 2b trigger condition in Part 1 pipeline specification.`

Deployment-target applicability: Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | Convergence map artifact stored as `Stage 2b artifact:` in plan or commit message; web search availability per deployment target (web search tool required) |
| Claude Chat | Convergence map produced inline in conversation; `Stage 2b artifact:` cites conversation date and topic instead of plan/commit path; web search generally available on this deployment target for prior art queries |

*Self-check: subject `Every pipeline execution producing a governance artifact` is bare; permitted values include two `None —` exits covering non-governance artifacts and recent-search cases; `Enforced by:` field present (RULE-023 satisfied); `Deployment-target applicability:` per-target table present (RULE-031 satisfied — rule body cites plan / commit message infrastructure).*

---

### Rule 19: Deployment-target applicability for infrastructure-dependent rules [RULE-031]

> **Scope:** Authoring

**Every rule statement that references deployment infrastructure must contain a `Deployment-target applicability:` field.** Permitted values:
- The literal phrase **`Applies uniformly across deployment targets`**, *or*
- `Per-target applicability: <table or list>` naming each deployment target and how the rule differs there, *or*
- `None — rule body contains no infrastructure tokens (no \`hook\`, \`.claude/\`, \`tests/\`, \`docs/plans/\`, \`backlog\`, \`[PA-\`, \`[ERR-\`, repository file path)`.

A rule that names hook / test / file-path / backlog infrastructure but doesn't declare per-target applicability silently produces hollow guidance on deployment targets lacking that infrastructure. The trigger fires on the infrastructure tokens; the permitted values cite which deployment target lacks the infrastructure and what fallback applies.

**Deployment targets** (canonical taxonomy; expanded rationale in [`prompt-authoring-background.md § Multi-Deployment-Target Guidance Rationale`](prompt-authoring-background.md#multi-deployment-target-guidance-rationale)):

| Deployment Target | Includes | File system | Hooks | Tests | Backlog |
|---|---|---|---|---|---|
| **Claude Code Local** | Claude Code on CLI / Desktop app / VS Code (per `platform-guide.md`) | Persistent | Available | Available | Available |
| **Claude Code Remote** | Claude Code on Web / Mobile (per `platform-guide.md`) | Session-persistent | Available | Available (Python deps auto-install) | Available |
| **Claude Chat** | claude.ai chat interface (no Claude Code; future MCP / custom-connector deployment target) | None — uploads only | None | None | None |

**Per-target applicability table form** — collapsed two-row form by default:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | <full behavior> |
| Claude Chat | <fallback or `Not enforceable on this deployment target — manual author responsibility`> |

Expanded three-row form permitted when Code Local and Code Remote diverge (e.g., subagent concurrency, worktree availability).

**Output-scope rules exempt.** RULE-013 through RULE-019 (output-scope rules governing tokens emitted in causal claims) inherit `Deployment-target applicability: Applies uniformly across deployment targets` because output H40 dynamics are context-pressure phenomena and operate identically on every deployment target. They require no per-target table.

**Worked example.** RULE-023's `Enforced by:` permitted values include hook / test / skill / backlog ID. Per-target applicability:

| Deployment Targets | Behavior |
|---|---|
| Claude Code (Local + Remote) | All four permitted values available — hook name, test file, skill invocation, or `Documentation-tier only — backlog: <ID>` |
| Claude Chat | Only `Not enforceable on this deployment target — manual author responsibility` permitted; the named-tier values reference infrastructure that does not exist on this deployment target |

Trigger features: rule body contains `hook`, `.claude/`, `tests/`, `docs/plans/`, `backlog`, `[PA-`, `[ERR-`, or a path-like token `<segment>/<segment>` referring to a repository file; or `None — no infrastructure tokens`.

Borderline cases:
- RULE-023 (`Enforced by:` field naming hook / test / skill / backlog ID) — in-scope; trigger `hook`, `tests/`, `backlog` fires; per-target table required as shown above.
- RULE-001 (transformer rule shape) — out-of-scope; rule body names no infrastructure tokens; `None — rule body contains no infrastructure tokens` permitted value applies.

Prerequisites: RULE-021 (parallel structure for per-stage applicability), RULE-024 (synonym precedence convention used for deployment-target names).

Changes summary: Modifies RULE-011, RULE-023, RULE-025, RULE-028 (Stage 7c), RULE-030, and the Part 3 fabrication `[PA]` row by requiring per-target applicability declarations where each currently names infrastructure unconditionally.

Pipeline evidence: docs/plans/multi-surface-guidance.md § Stage 4 (synthesis) + Stage 5 (adversarial critique with sequestered v2 analysis); terminology migrated Surface → Deployment Target in v2.8.1 (see plan § Terminology Migration).

`Enforced by: rule-design-standards.md Quick-Reference Checklist row + author-side audit during plan completion ceremony self-compliance gate (CLAUDE.md).`

Deployment-target applicability: Applies uniformly across deployment targets (the rule itself is an authoring-time rule; authoring an instruction document happens on every deployment target).

*Self-check: subject `Every rule statement that references deployment infrastructure` is bare; `Deployment-target applicability:` permitted values include `None — no infrastructure tokens` for non-infrastructure rules; the rule's own `Deployment-target applicability: Applies uniformly across deployment targets` declaration satisfies self-application.*

---

## Part 3: Honest-Framing Vocabulary

Any AI output that contains one of these phrases in a causal claim or conclusion is malformed — rewrite using the **Positive replacement form** in the right column.

**Banned-phrase rules require positive replacements.** A row that bans a phrase without naming what to write instead is incomplete: the AI invents a replacement, often a synonym ("evidently" for "obviously") that shares the original's failure mode at one level of indirection. Every row below — including catch-alls — must give a positive replacement form.

### Anthropomorphism — Phrases Implying AI Agency, Intention, or Moral Failure

| Flagged phrase | Replacement | Positive replacement form |
|----------------|-------------|---------------------------|
| "I should have" | context-window saturation / salience competition | *"The format rule that would have caught this is missing — propose: [rule]."* |
| "I forgot to" | lost-in-the-middle effect / context drift | *"The trigger for [step] was not present in the output shape — add [trigger artifact]."* |
| "I treated" | output-shape continuation pressure | *"Output shape continued from [prior turn] without a re-trigger; missing format rule: [rule]."* |
| "lack of discipline" | missing format rule / structural Rule 1 violation | *"No format rule fires on [observable condition]; add one: [proposed rule]."* |
| "be more careful" | add structural enforcement — format rule or hook | *"Promote enforcement to [hook \| skill \| test]; specify: [enforcement step]."* |
| "remember to" | format rule with output shape / skill invocation | *"On [observable trigger], emit [required output element]."* |
| "try harder" | structural fix: hooks > skills > tests > docs | *"Move enforcement up the tier list: from [current tier] to [target tier], implement: [step]."* |
| "I failed to" | runtime self-monitoring failure (missing format rule) | *"No format-rule trigger fired for [observable condition]; add: [proposed rule]."* |
| "AI forgetfulness" | context-window saturation / lost-in-the-middle | *"Salience dropped past [position]; relocate the trigger to [closer-to-emission location]."* |
| "not careful enough" | salience competition / context drift | *"Trigger lost salience under [competing demand]; add structural anchor: [artifact]."* |
| "paid more attention" | format-rule enforcement | *"Add a format rule firing on [observable condition]: [rule statement]."* |

**Catch-all:** Any sentence with the AI as grammatical subject of a mental-state verb (`should`, `forgot`, `remembered`, `intended`, `tried`, `noticed`, `realized`, `paid attention`). Trigger: grep the sentence for `^I (should|forgot|remembered|intended|tried|noticed|realized|paid)`. Replacement form: *"On `[observable condition]`, emit `[required output element]`."* If no replacement of that form can be supplied, downgrade the diagnosis to *"Mechanism unknown — requires structural investigation"* before publishing.

**Worked example.** *"I should have noticed the missing marker."* → trigger fires (`I should have`). Mechanism replacement: *"No format rule fired on the missing-marker condition."* Positive replacement: *"On a causal-claim sentence emitted without `[Verified]` or `[Hypothesis]`, emit a `Stipulation:` line stating why no marker is available."*

### Hallucination — Phrases Asserting Confidence Without Evidence

| Flagged phrase | Replacement | Positive replacement form |
|----------------|-------------|---------------------------|
| "clearly the cause is" | "one hypothesis is [Hypothesis: what would prove this wrong?]" | *"`[Hypothesis: <claim> — disconfirmation: <cheapest observation>]`"* |
| "obviously" | remove; replace with the specific observation | *"`[Verified: <source>]` <observation>"* |
| "the root cause is [X]" (unqualified) | "the root cause candidate is [X] [Hypothesis: what would prove this wrong?]" | *"Root cause candidate: <X>. `[Hypothesis: disconfirmation = <cheapest observation>]`"* |
| "this definitely caused" | "this may have contributed [Hypothesis: disconfirmation]" | *"Contributed to the failure (one of multiple). `[Hypothesis: disconfirmation = <observation>]`"* |
| "always causes" | "has been associated with [Verified: source or prior failure log]" | *"Associated with <effect> in <N> prior failures. `[Verified: <log link>]`"* |
| "this is definitely" | "based on available evidence, [Verified/Hypothesis]" | *"`[Verified: <source>]` shows <observation>."* OR *"`[Hypothesis: <claim> — disconfirmation: <observation>]`"* |
| "it is clear that" | remove; state the evidence directly | *"`[Verified: <source>]` shows <observation>; the inference is <claim>."* |

**Catch-all:** Any causal claim (Rule 1.1 trigger features: `because`, `caused by`, `due to`, `→`) stated as fact without `[Verified: source]` or `[Hypothesis: disconfirmation]`. Positive form: every causal claim ends with one of the two markers. If neither can be supplied, downgrade the claim to *"candidate cause, requires investigation"* before publishing.

**Worked example.** *"The deploy failed obviously because the cache wasn't cleared."* → triggers fire (`obviously`, `because`). Replacement: *"The deploy failed [Hypothesis: cache wasn't cleared — disconfirmation: re-run with `cache clear` and observe whether the failure recurs]."*

### Fabrication — Phrases Asserting External Facts Without a Source

| Flagged phrase | Replacement | Positive replacement form |
|----------------|-------------|---------------------------|
| "as documented" (without `[Verified: source]`) | "[Verified: source needed — cite specific documentation]" | *"As documented in `[Verified: <file:line> or <URL>]`."* |
| "it is known that" (without source) | "[Hypothesis: what would confirm or falsify this?]" | *"`[Hypothesis: <claim>]`. Cheapest verification: <observation>."* |
| "the platform always" (without source) | "[Hypothesis: verify against platform documentation]" | *"`[Hypothesis: platform behavior <claim> — verify against <doc URL>]`."* |
| "known issue" (without `[PA]` tag) | "suspected issue — confirm via known patterns search; add `[PA]` tag if found" | *"Suspected pattern. Search anti-patterns; if matched, mark `[PA-<id>]`. If not, mark `[Hypothesis]`."* **Per-target note:** on Claude Chat, `docs/reference/project-anti-patterns.md` is not accessible; permitted form is *"suspected pattern (anti-patterns catalog not accessible on this deployment target)"* — `[PA]` tag is unavailable. See RULE-031 / Rule 19. |
| "by design" (without source) | "[Verified: source needed — cite design document or specification]" | *"By design per `[Verified: <design doc:section>]`."* |
| "this is expected behavior" (without source) | "[Hypothesis: source needed to confirm expectation]" | *"Expected per `[Verified: <spec or doc reference>]`."* |

**Catch-all:** Any sentence whose subject is an external system, platform, or third party (e.g., `the platform`, `the API`, `the docs`, `<library>`, `<service>`) coupled with a behavior claim — stated without an inline `[Verified: <source>]` tag. Trigger: grep the sentence for proper-noun or definite-article subjects with verbs like `does`, `returns`, `behaves`, `expects`, `requires`. Positive form: append `[Verified: <file:line | URL | command output>]` inline; if no source can be supplied, downgrade to `[Hypothesis: <claim> — verification path: <command or doc URL>]`.

**Worked example.** *"The platform always rate-limits at 100 requests per minute."* → triggers fire (`The platform`, `always`). Replacement: *"The platform rate-limits at 100 requests per minute [Verified: docs/api/rate-limits.md:42]."* If unsourced: *"[Hypothesis: platform rate-limits at 100 rpm — verification path: send 101 requests in 60s and observe the 429 response]."*

### Compliance Theater — Structural Patterns That Pass Phrase-Level Checks While Violating Rule Intent

Compliance theater is a structural failure mode parallel to Anthropomorphism, Hallucination, and Fabrication, but it operates one level up: the output passes every phrase-level check yet violates the rule's intent. The diagnostic question is *"if I removed the rule, would the output change?"* If no, the rule is producing surface compliance only.

| Pattern | Diagnosis | Positive replacement form |
|---------|-----------|---------------------------|
| Tools-used list with non-specific entries ("Reasoning. Analysis.") | Padding to satisfy a tools-list requirement; non-specific entries are uninformative and don't support the format rule's intent (audit trail of investigation). | *"Tools used: <named tool> (<specific input/output>). For tools considered but not used: <tool> — <one-line reason>."* |
| Defects identified for every domain regardless of evidence | Quota-satisfying output (Rule 5.1 violation in disguise); fabricated defects fill the slot | *"Domain X — None at threshold. Reason: <one-line justification>."* |
| Source-checks listed when no checking occurred | Fabrication per the Fabrication catch-all, applied to a citation list | *"Sources checked: <name> (`[Verified: <link>]` returned <observation>). For sources not checked: <name> — <reason>."* |
| Markers applied to non-claims to raise marker density | Surface compliance with Rule 8 / Rule 1.1 — markers attached to descriptive prose to satisfy a coverage check | *"Markers attach to causal/definitional claims only; descriptive prose stays unmarked."* |
| Multi-field templates filled with identical or formulaic content across rows | Field-count compliance without field-level differentiation (Rule 5.2 violation) | *"<field>: minimal — <one-line reason>."* OR substantive differentiation per row. |
| Adversarial-critique stage that reproduces the synthesis recommendation | Generation/critique sequestration violation (Part 1 §Adversarial sequestration) | *"Critique stage produces ≥1 challenge naming a specific assumption from synthesis; if no challenge can be produced, sequestration was inadequate — re-run with stricter isolation."* |

**Catch-all:** Output that passes structural checks while the rule's intent is unmet. Surface triggers (any one fires the diagnosis):
- list entries shorter than 3 words in a slot meant to record substance (`Tools used:`, `Sources checked:`, defect lists),
- ≥3 cells in a multi-row template containing the same string verbatim,
- ≥2 marker-bearing sentences (`[Verified]` / `[Hypothesis]`) without one of Rule 1.1's causal trigger tokens (`because`, `caused by`, `due to`, `→`),
- adversarial-critique stage output that quotes the synthesis recommendation without contradiction tokens (`but`, `however`, `unless`, `if instead`).

Positive form: for each rule whose enforcement is suspect, name in the output the specific behavior change the rule produces and one observable consequence beyond the structural check. *"Rule X enforces Y; this output evidences Y by Z."* If Z cannot be supplied, the rule is producing compliance theater on this artifact.

---

## Quick-Reference Checklist

Before submitting any authored prompt or instruction:

**Part 1 — Pipeline (run if your output spans multiple stages)**
- [ ] Pipeline includes adversarial critique stage before refinement (Stage 5)
- [ ] Pipeline trigger condition uses observable artifact conditions, not judgment qualifiers (Rule 3 applied to Part 1)
- [ ] Cross-stage handoffs are specified as named fields in stage N's output and named inputs in stage N+1's TASK (§Cross-stage handoff structure)
- [ ] Generation stages have a `Sequestered:` line listing downstream candidates absent from input (§Adversarial sequestration)
- [ ] Governance artifact outputs (guide, rule set, standard, instruction template) include a Stage 2b Prior Art & Convergence Check artifact (RULE-030 / Rule 18)
- [ ] Full pipeline outputs (and durable lightweight outputs) include a Stage 7 Whole-Output Coherence Review with PASS/CORRECTED/BLOCKED verdict (RULE-028 / Rule 16)

**Part 2 — Rule shape (apply to every authored rule)**
- [ ] Rule is transformer-shaped (subject is a surface feature; trigger fires on the authoring act) — not conditional/property-claim shape (RULE-001 / Rule 1)
- [ ] Format rules appear before procedural guidance in any list (RULE-003 / Rule 2)
- [ ] Every rule can be verified by reading the output — no judgment qualifiers (RULE-004 / Rule 3)
- [ ] Rule triggers are behaviors, not media — passes rename test (RULE-005 / Rule 4)
- [ ] Investigation templates include Observed / Hypotheses slots (RULE-006 / Rule 5)
- [ ] New rules include a falsifiable behavioral test condition (RULE-009 / Rule 6)
- [ ] Existing artifacts were audited for compliance with any new rule (RULE-011 / Rule 7)
- [ ] Investigation-concluding outputs carry `[Verified]` / `[Hypothesis]` tags (RULE-013 / Rule 8)

**Part 2 sub-clauses — fire when the rule has the listed surface feature**
- [ ] Class-of-utterance rules (`every X`, class noun in subject) carry `Trigger features:` + `Borderline cases:` with ≥2 examples (RULE-002 / Rule 1.1)
- [ ] Count-bearing rules (digit / `≥` / `at least`) carry a `"None at threshold"` exit OR a conditional reformulation (RULE-007 / Rule 5.1)
- [ ] Multi-field templates (≥4 required fields) carry a `Brevity allowance:` line (RULE-008 / Rule 5.2)
- [ ] Falsifiability clauses carry threshold + horizon + role tokens (RULE-010 / Rule 6.1)
- [ ] Procedural-constraint rules (`halt|block|wait|must not|refuse|stop`) carry `Applies in all contexts` OR an `Override:` line (RULE-012 / Rule 7.1)
- [ ] Procedural commands (`halt|reconsider|audit|review|verify|reflect|check`) carry `Trigger:` + `Steps:` + `Output:` blocks (RULE-020 / Rule 9)
- [ ] Pipeline-spanning rules (`stage`, `pipeline`, numbered stage refs) carry `Applies uniformly across stages` OR a `Per-stage applicability:` subsection (RULE-021 / Rule 10)
- [ ] Every Rule N section ends with a `Self-check:` line naming the rule applied and the surface feature (RULE-022 / Rule 11)
- [ ] Unconditional behavioral obligations (`unconditionally`, `fires unconditionally`, `without exception`, `regardless of context`) carry an `Enforced by:` field naming the structural gate (RULE-023 / Rule 12)
- [ ] Multi-step skills with adjacent trigger vocabulary (≥2 step headings with trigger-bearing bodies) carry `Closed synonym list:` per collision-pair step and one `Precedence:` per collision pair (RULE-024 / Rule 13)
- [ ] Section headings containing stable-ID tokens (`[RULE-`, `[T5.`, `[ERR-`, etc.) carry a `Pipeline evidence:` field (RULE-025 / Rule 14)
- [ ] Section headings containing stable-ID tokens carry `Prerequisites:` and `Changes summary:` fields (RULE-026 / Rule 15)
- [ ] Rule scope declarations (Authoring/Output/Process) were assigned using the three-question decision procedure (RULE-029 / Rule 17)
- [ ] Pipeline definitions carry stable `[PIPELINE-NNN]` IDs and appear in the Part 1 Pipeline Registry (RULE-025 trigger updated to recognize `[PIPELINE-` prefix)
- [ ] Infrastructure-dependent rules (rule body contains `hook`, `.claude/`, `tests/`, `docs/plans/`, `backlog`, `[PA-`, `[ERR-`, or repository file path) carry a `Deployment-target applicability:` field with `Applies uniformly across deployment targets` OR a per-target table (RULE-031 / Rule 19)
- [ ] Per-target declarations match the canonical three-target taxonomy (Claude Code Local, Claude Code Remote, Claude Chat) defined in RULE-031

**Part 3 — Honest-framing (apply to any AI causal or investigative output)**
- [ ] No flagged phrases from honest-framing tables (Anthropomorphism / Hallucination / Fabrication)
- [ ] Every banned-phrase row carries a positive replacement form, including catch-all rows
- [ ] Output passes the compliance-theater surface checks — no short list entries in substance slots, no duplicate cells, no markers on non-causal sentences, no critique that quotes synthesis without contradiction tokens (§Compliance theater)

**SKILL.md / authoring conventions**
- [ ] Claude-facing guide contains format obligations only — no rationale prose (two-file separation design decision)
- [ ] All numbered references in co-present numbered sequences name their referent explicitly (e.g., "Rule Design Standards Rule 1" not "Rule 1" when another numbered list is present)
- [ ] Section introductions and framing prose use observable-output conditions, not pre-emission or internal-scan instructions (Rule 1 applied to prose)
- [ ] Every reviewer-facing tip or instruction names its delivery point and observable trigger — not a parenthetical aside or prose note (Rule 3 applied to SKILL.md authoring)
- [ ] When a step implements a multi-pass cycle, a loop-control header block is present naming Entry, Body, and Exit as distinct labeled elements (Rule 1 applied to SKILL.md loop authoring)

---

## Relationship to Existing Material

| Concept | Defined in | This guide's relationship |
|---|---|---|
| H40 (awareness ≠ prevention) | `docs/design/golem-design.md` §18.1 | Part 2 is the prescriptive authoring companion |
| Stimulus-bound triggers | `docs/design/golem-design.md` §18.1 | Format rules are the documentation-tier instance |
| Triggerless rules | `docs/reference/project-anti-patterns.md` | Rule 1 is the prevention; that entry is the diagnosis |
| Three-tier enforcement (hooks > skills > tests > docs) | `docs/reference/project-anti-patterns.md` | This guide governs the documentation tier |
| Constraint stored as documentation | `docs/reference/project-anti-patterns.md` | Rules 1 and 3 prevent the prose version |
| Process gates added without re-scanning | `docs/reference/project-anti-patterns.md` | Rule 7 codifies the prevention |
| Incident reports masquerading as principles | `docs/reference/project-anti-patterns.md` | Rule 3 (narrow and concrete) prevents this |
| Pipeline design rationale | `docs/reference/prompt-authoring-background.md` | 8 failure modes the pipeline addresses |
| Deployment targets (Code Local, Code Remote) | `docs/platform-guide.md` | RULE-031 extends the taxonomy with Claude Chat as a third deployment target (also a future MCP / custom-connector target) |
| Multi-deployment-target guidance rationale | `docs/reference/prompt-authoring-background.md` § Multi-Deployment-Target Guidance Rationale | Explains why infrastructure-dependent rules need per-target applicability declarations |
| Pipeline naming convention | `docs/reference/prompt-authoring-background.md` § Pipeline Naming Convention Rationale | Explains stable `[PIPELINE-NNN]` IDs and the registry table pattern |

---

## Changelog

v2.9.0 — 2026-05-18: Extract PIPELINE-001 stage definitions to standalone file (PIPELINE-001-EXTRACT).
- **Stage 1–7 definitions removed:** replaced with a pointer to `pipeline-001-prompt.md`, the standalone exportable specification. Reduces this file from ~1,643 to ~1,410 lines.
- **No rule-ID changes:** RULE-P01 through RULE-P04, Control Levers, and PIPELINE-002 remain unchanged in this file as the canonical rule-ID reference.
- **Authoring methodology:** PIPELINE-001 itself (meta-authoring); Stage 7 verdict: PASS.

v2.8.7 — 2026-05-16: Stage 7 termination — Primary + Dissent capture supersedes 3-iteration bound (FB-044).
- **Stage 7 Termination paragraph rewritten:** removed the 3-iteration arbitrary bound (per FB-044, RCA on FB-005: numeric literal lacked calibration source). Three named exits now: `PASS`, `PRIMARY+DISSENT` (stable disagreement captured with both positions in verification log), `ESCALATED` (degenerate exits only — Stage 7 cannot produce any verdict). No iteration cap on the CORRECTED/BLOCKED loop.
- **Verdict options list:** added `PRIMARY+DISSENT` as a fourth verdict option; ESCALATED narrowed to degenerate cases only.
- **Hypothesis marker:** prior v2.8.2 hypothesis (about unbounded loops converging on local rewrites) marked superseded 2026-05-16; new hypothesis declared (Primary+Dissent preserves the dissent signal the bound was masking; disconfirmation = 20-run replay showing PRIMARY+DISSENT-exited pipelines have higher post-implementation revision than PASS-exited pipelines, indicating the dissent should have blocked).
- **RULE-028 permitted values:** added `Stage 7 verdict: PRIMARY+DISSENT — <primary> // <dissent>` form; ESCALATED entry rewritten to name "degenerate exit" rather than "termination bound."
- **Test:** `tests/test-pipeline-stage7-termination.sh` extended to 8 structural assertions (Primary present, Dissent present, ESCALATED for degenerate exits, no-iteration-cap discipline check, prior assertions for Enforced by / human routing / uniform applicability). Initial run after rewrite: 5/8 passing; final run: 8/8.
- **Source:** FB-044 (RCA on FB-005) in `.walkthrough-feedback.md` walkthrough Round 2. Design decision recorded as "Option B" in walkthrough Round 1 disposition.
- **Execution context:** `None — applied via walkthrough Step 4b implementation, not a PIPELINE-001 run`. This patch was not authored as a PIPELINE-001 pipeline run; it was a walkthrough Step 4b implementation of a fixed design decision (Option B from walkthrough Round 1 disposition) by the main session on Claude Code Remote (Mobile). Stage 7 sub-checks and the Stage 2b convergence-map propagation exit do not apply because no Stage 2b ran. The TDD test cycle (`tests/test-pipeline-stage7-termination.sh` 5/8 → 8/8) is the structural gate that landed this patch — see Test field above.

v2.8.6 — 2026-05-13: Stage 2b.1 — Independent retrieval verification of convergence map + Stage 7 sub-check 7f.
- **New Stage 2b.1 sub-stage:** `### Stage 2b.1: Independent retrieval verification of convergence map` inserted between Stage 2b and Stage 3. Closes G2 (Stage 2b is self-attested — the LLM running the literature search shares all training-time priors with the LLM that produced the rule under review). Sub-stage runs in a structurally isolated subagent per RULE-P03, takes Stage 2b's `Convergence map:` rows as INPUT (with author of rule under review `Sequestered:` per RULE-P02), and emits per-row `CONFIRMED` / `MISCITED` / `UNFOUND` verdicts in a four-column OUTPUT table.
- **Verdict semantics:** `Stage 2b.1 verdict: PASS` when `MISCITED + UNFOUND` rows ≤ 30% of total table rows (proceed to Stage 3); `Stage 2b.1 verdict: BLOCKED` when threshold exceeded (route to Stage 6 for correction, re-run Stage 2b.1). The 30% threshold tolerates inevitable verbatim-match drift in citation phrasing while flagging convergence maps where a substantive minority of claims fail independent verification.
- **Falsification:** on a 20-output replay of historical Stage 2b outputs, if `MISCITED + UNFOUND < 10%` system-wide under isolated-subagent verification, the self-attestation gap is empirically smaller than feared and this sub-stage should be downgraded to optional. Replay study deferred to `[PIPELINE-001-2B-REPLAY]` per CLAUDE.md plan-design gate `[GATE-PLAN-SAMPLE-SIZE]` (sample-size justification requires N≥20 historical Stage 2b outputs; this authoring run filed the backlog item rather than running the study inline).
- **Stage 7 sub-check 7f:** added `**7f — Stage 2b.1 verification table consistency:**` to Stage 7's check sequence (between 7e and the Verdict block); verifies OUTPUT table presence when Stage 2b ran in non-degenerate form, enumerated verdict strings, and 30%-threshold consistency. Stage 7's Self-check line updated to name 7f in addition to 7e.
- **Test:** `tests/test-pipeline-stage-2b1-independence.sh` (34 structural assertions: Stage 2b.1 heading present and ordered between Stage 2b and Stage 3, trigger references Stage 2b's `Convergence map:` and propagates the `None —` exit, INPUT block declares `Sequestered:` per RULE-P02, `Execution context:` field with Local/Remote default and Claude Chat fallback per RULE-P03, OUTPUT table headers, three permitted verdict strings, 30% threshold, 10% falsification on 20-output replay, `Enforced by:` Stage 7 sub-check 7f per RULE-023, `Deployment-target applicability:` per RULE-031, Self-check per RULE-022, Stage 7 sub-check 7f references Stage 2b.1, changelog v2.8.6 self-application declares Isolated subagent — fresh context).
- **Source:** `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § Phase B1 + § G2. Backlog ID: `[PIPELINE-001-2B-INDEP]` (closed by this commit); replay-study backlog ID: `[PIPELINE-001-2B-REPLAY]` (filed UNBLOCKED). T5.37 (prior-art currency gate) cited as adjacent / orthogonal concern (currency vs. independence-of-verifier).
- **Self-application:** `Execution context: Isolated subagent — fresh context` per RULE-P03 Remote row (this authoring run executed as an isolated opus-tier subagent spawned from a Claude Code Remote session, with the B1 plan brief as the sole INPUT; no carried state from the main session). The sub-stage being authored thereby satisfies the isolation guarantee it requires of every future Stage 2b.1 invocation — canonical first application on its own authoring artifact.

v2.8.5 — 2026-05-13: Citation-existence linter (`tools/check-citations.py`) — Stage 7c test-tier promotion.
- **Stage 7c `Enforced by:` (test-tier):** sub-check 7c now cites `tools/check-citations.py` as the test-tier enforcement on Claude Code (Local + Remote), promoting citation-existence verification from author-discipline-tier to test-tier per the three-tier enforcement model (Hooks > Skills > Tests > Documentation). Claude Chat retains author-discipline-tier enforcement (`[7c limited: file paths unverifiable on this deployment target]`).
- **Linter scope:** resolves `[file:line]` bracketed references (file-exists + line-within-count), markdown links (target-exists + anchor-slug match), and `RULE-NNN` / `ERR-NNN` / `PIPELINE-NNN` / `T5.NN` ID references against their authoritative index files (`rule-id-conversion.md`, `error-catalog.md`, `rule-design-standards.md` Pipeline Registry, `framework-backlog.md`). Exits non-zero if any reference is unresolvable. Stdlib-only Python 3; no external dependencies.
- **TDD:** `tests/test-citation-linter.sh` (12 structural assertions: script exists + executable, fixtures exist, exits non-zero on broken fixture, stderr mentions each of 5 broken references by name, count ≥5, exits zero on good fixture). Initial run: 3/12 passing. Final run: 12/12 passing.
- **Fixtures:** `tests/fixtures/citation-broken.md` (5 deliberate broken references), `tests/fixtures/citation-good.md` (4 valid references — no false positives).
- **Self-application:** `Execution context: Isolated subagent — fresh context` per RULE-P03 Remote row (this authoring run executed as an isolated sonnet-tier subagent spawned from a Claude Code Remote session, with the B2 plan brief as the sole INPUT; no carried state from the main session).
- **Source:** `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § Phase B2. Backlog ID: `[PIPELINE-001-7C-LINTER]`.

v2.8.4 — 2026-05-13: RULE-P03 Stage execution isolation + Stage 7 sub-check 7e.
- **New Part 1 structure:** `### Stage execution isolation [RULE-P03]` inserted between RULE-P02 and RULE-P04 (slot order P02 → P03 → P04, restoring the intended numerical sequence after RULE-P04's authoring-order insertion in v2.8.3). Bare-subject transformer form: every pipeline stage invocation must contain an `Execution context:` line with permitted values (i) `Isolated subagent — fresh context, INPUT block is the only carried state` (default on Claude Code Local + Remote), (ii) `Sequential same-context — degraded execution, candidates leak across stages` (sole permitted value on Claude Chat; downgrades `Decision:` / `Verdict:` to advisory), or (iii) `None — single-stage prompt with no inter-stage execution mode question`. Closes G1 (execution-mode isolation unstated) and subsumes G3 (Stage 5 evaluator-not-designer unenforced) from the critique-of-pipeline-001 plan.
- **Per-target table:** three-row deployment-target table (Claude Code Local / Claude Code Remote / Claude Chat) declaring `Isolated subagent` availability and the default value when unspecified.
- **Stage 7 sub-check 7e:** added `**7e — Execution-context consistency [RULE-P03]:**` to Stage 7's check sequence (between 7d and the Verdict block); cites RULE-P03 by ID and verifies the `Execution context:` field on every stage invocation against the per-target row for the current deployment target. Stage 7's Self-check line updated to name 7e.
- **Hypothesis marker:** same-context execution produces inter-stage convergence on a single reasoning trajectory irrespective of RULE-P02 sequestration; disconfirmation via 20-pipeline replay comparing Stage 5 / Stage 4 divergence rates between same-context and isolated-subagent runs.
- **Trigger features:** any pipeline stage specification containing a `TASK:` or `INPUT:` block, or stage labels (Stage N / Framing / Routing / Analysis / Synthesis / Critique / Refinement); `None — single-stage prompt with no downstream consumer stage` permitted exit.
- **Test:** `tests/test-rule-p03-execution-isolation.sh` (26 structural assertions: stable ID, short title, slot order between RULE-P02 and RULE-P04, three permitted values, per-target table with three deployment-target rows, hypothesis + disconfirmation, cross-reference to RULE-P02, `Enforced by:` per RULE-023, `Deployment-target applicability:` per RULE-031, `Self-check:` per RULE-022, `Trigger features:` per RULE-002, `Pipeline evidence:` linkage, Stage 7 sub-check 7e referencing RULE-P03 by ID, changelog v2.8.4 self-application declaring `Isolated subagent — fresh context`).
- **Source:** `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § Phase A1 + § G1. Backlog ID: `[PIPELINE-001-P03]`.
- **Propagation:** `docs/reference/rule-id-conversion.md` v1.6.0 adds the RULE-P03 row to Part 1 Structures; `docs/reference/prompt-authoring-background.md` § "Why Execution Isolation ([RULE-P03] / Part 1)" companion section added; `docs/reference/project-anti-patterns.md` § Process Patterns gains the "Claude Code Remote (Mobile / Web) conflated with Claude Chat" anti-pattern; v2.8.3 changelog Self-application line corrected (see v2.8.3 entry below — Mobile was misclassified as Claude Chat).
- **Self-application:** `Execution context: Isolated subagent — fresh context` per the Remote row of this rule's own per-target table. The A1 authoring run executed as an isolated subagent (opus tier) spawned from a Claude Code Remote (Mobile) main session per CLAUDE.md § Subagent Execution, with the plan's A1 brief as the INPUT block and no carried state from the main session beyond that brief — the canonical first application of RULE-P03 to its own authoring artifact. The rule satisfies itself.

v2.8.3 — 2026-05-12: RULE-P04 Critique grounding.
- **New Part 1 structure:** `### Critique grounding [RULE-P04]` inserted after RULE-P02. Bare-subject transformer form: every adversarial-critique artifact must contain a `Verbatim quotes:` line with permitted values (i) ≥3 verbatim quotes from the artifact under review each carrying a section or line-number reference, or (ii) `None — target is sequestered from this stage's input per RULE-P02 (state which downstream stage receives the target)`. Closes G6 (adversarial-critique-must-quote) from the critique-of-pipeline-001 plan.
- **Hypothesis marker:** zero-quote critiques generated without source contact reinvent target constructs; disconfirmation via 20-critique replay comparing source-document-construct citation rates.
- **Trigger features:** artifact heading or filename containing `critique`, `review`, `assessment`, `evaluation`, or `audit` of a named internal target; `None — target is unnamed, external, or conversational` permitted exit.
- **Test:** `tests/test-rule-p04-critique-grounding.sh` (18 structural assertions: stable ID, short title, field name, both permitted values, hypothesis + disconfirmation, trigger features, `Enforced by:` per RULE-023, `Deployment-target applicability:` per RULE-031, `Self-check:` per RULE-022, self-application citation to authoring plan, `Pipeline evidence:` linkage).
- **Source:** `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § Phase A3 + § G6. Backlog ID: `[PIPELINE-001-P04]`.
- **Insertion position:** after RULE-P02. When `[PIPELINE-001-P03]` (Stage execution isolation) lands later in a Claude Code Local session, RULE-P03 inserts between RULE-P02 and RULE-P04; the ordering reflects authoring sequence, not rule precedence.
- **Self-application:** the authoring plan itself contains three verbatim quotes from this document — Stage 2b's "None — pipeline output is not a governance artifact" exit at line 107, Stage 7's "Loop until PASS" formulation at line 204, RULE-P02's INPUT-block obligation at lines 275–278 — satisfying RULE-P04 on its own authoring artifact. `Execution context: Isolated subagent — fresh context` per draft RULE-P03 Remote row (Claude Code Remote / Mobile session). (Mobile misclassified as Claude Chat in original v2.8.2 / v2.8.3 entries; corrected 2026-05-13 during RULE-P03 authoring per the per-target table — Mobile is Claude Code Remote per CLAUDE.md's three-target taxonomy, and Remote's default is `Isolated subagent — fresh context`, not the Claude Chat fallback.)

v2.8.2 — 2026-05-12: Stage 7 termination bound — ESCALATED verdict.
- **Stage 7 verdict block:** added `ESCALATED` as a fourth verdict option; new `**Termination.**` paragraph specifies three-iteration bound on CORRECTED/BLOCKED returns, full-check-trace requirement, and human-review routing with named-reviewer override. Closes the unbounded "Loop until PASS" gap.
- **RULE-028 permitted values:** added `Stage 7 verdict: ESCALATED — <full check trace>` form with `Human-review override:` plan-log requirement before IMPLEMENTED.
- **Test:** `tests/test-pipeline-stage7-termination.sh` (6 structural assertions: ESCALATED present, three-iteration bound, `Enforced by:` declared, human-review routing, uniform deployment-target applicability).
- **Source:** `/root/.claude/plans/critique-of-pipeline-001-evaluate-modular-shell.md` § Phase A2 + § G4. Backlog ID: `[PIPELINE-001-S7-BOUND]`.
- **Self-application:** this patch was authored on a Claude Code Remote (Mobile) session (`Execution context: Isolated subagent — fresh context` per draft RULE-P03 Remote row); Stage 7 sub-checks 7a/7b/7d run on the patch itself, 7c limited per RULE-031 / Stage 7c per-target note. Stage 7 verdict: PASS. (Original v2.8.2 entry said Claude Chat with `Sequential same-context — degraded execution`; corrected 2026-05-13 during RULE-P03 authoring — Mobile is Claude Code Remote, not Claude Chat, per CLAUDE.md's three-target taxonomy.)

v2.8.1 — 2026-05-08: Terminology migration — Surface → Deployment Target (intra-branch rename, follows v2.8.0 review).
- **Conceptual noun rename:** `Surface` → `Deployment Target` throughout RULE-031, the per-target tables on RULE-011 / RULE-023 / RULE-025 / RULE-028 / RULE-030, the Stage 7c per-target note, the Part 3 fabrication `[PA]` per-target note, the Quick-Reference Checklist rows, and the Relationship table rows. Justification: `Surface` was inherited from user-stated requirements without a rename test; `Deployment Target` matches CI/CD vocabulary and accommodates Claude Chat as a future MCP / custom-connector deployment target.
- **Field name rename:** `Surface applicability:` → `Deployment-target applicability:` (singular field name, parallels `Pipeline applicability:` from RULE-021).
- **Permitted value rename:** `Applies uniformly across surfaces` → `Applies uniformly across deployment targets`; `Per-surface applicability:` → `Per-target applicability:`.
- **Column header form:** Single-target-per-row tables use `Deployment Target` (singular); multi-target-per-row tables (per-target applicability) use `Deployment Targets` (plural — accepts multi-target consolidation per row).
- **Canonical Chat fallback rename:** `Not enforceable on this surface — manual author responsibility` → `Not enforceable on this deployment target — manual author responsibility`.
- **Companion document:** `Multi-Surface Guidance Rationale` → `Multi-Deployment-Target Guidance Rationale` in `prompt-authoring-background.md`. Anchor link updated.
- **Hard rename, no synonym retention:** v2.8.0 was branch-local; no external consumers exist. RULE-024 closed-synonym-list mechanism not invoked.
- **Plan file:** `docs/plans/multi-surface-guidance.md` retains its filename for git-history continuity; § Terminology Migration appended to the otherwise frozen plan body.

v2.8.0 — 2026-05-08: Multi-surface guidance + explicit pipeline naming.
- **Pipeline Registry (Part 1)** — added registry table naming `[PIPELINE-001] Full Pipeline` and `[PIPELINE-002] Lightweight Pipeline`. Pipeline definitions now carry stable IDs; the `[PIPELINE-` prefix added to RULE-025 / RULE-026 trigger features. Future pipeline additions append rows; new-pipeline addition requires Full Pipeline run on the addition itself.
- **Lightweight Pipeline rename** — `Lightweight Variant` renamed to `Lightweight Pipeline` with closed synonym list per RULE-024 (`Lightweight Variant` retained as deprecated synonym; precedence: Lightweight Pipeline preferred for new references).
- **Rule 19 (RULE-031)** — Deployment-target applicability for infrastructure-dependent rules (renamed in v2.8.1; originally Surface applicability): every rule statement that references deployment infrastructure must contain a `Deployment-target applicability:` field. Permitted values: `Applies uniformly across deployment targets`, `Per-target applicability: <table>`, or `None — no infrastructure tokens`. Mirrors RULE-021 (per-stage applicability) for the per-target dimension.
- **Three-target taxonomy** — Claude Code Local (CLI / Desktop app / VS Code), Claude Code Remote (Web / Mobile), Claude Chat (claude.ai chat with no Claude Code infrastructure; also future MCP / custom-connector deployment target). Cross-references `docs/platform-guide.md` for the two Code targets; introduces Claude Chat as the third deployment target where hooks / tests / file system / backlog are unavailable.
- **Affected rules updated** — RULE-011, RULE-023, RULE-025, RULE-028 (Stage 7c), RULE-030, and the Part 3 fabrication `[PA]` row each gained a `Deployment-target applicability:` per-target table declaring how the rule degrades on Claude Chat.
- **Control Levers** — Model tier row gained per-target note: Claude Chat session model is fixed at session start; mid-pipeline escalation requires session restart.
- **RULE-025 misclassification authoring test** — full-pipeline runs on Claude Chat must use the new `Pipeline evidence: Claude Chat session — <date or topic>` permitted value, not the lightweight fallback.
- **Quick-Reference Checklist** — three new rows for `[PIPELINE-NNN]` IDs, `Deployment-target applicability:` field, and three-target taxonomy match.
- **Relationship table** — added rows for the deployment-target taxonomy, multi-deployment-target guidance rationale, and pipeline naming convention rationale (companion sections in `prompt-authoring-background.md`).

v2.7.0 — 2026-05-05: Walkthrough Round 2 feedback integration — Stage 2b actionability, Stage 7 loop-back, Rule 1 constraint, Part 2 preamble, Lightweight variant, Part 3 scope.
- **Stage 2b** — replaced prose convergence map with actionable output shape: added `Purpose:` naming AI NIH syndrome; `Decision:` field with 3 enumerated values; `Gap triage:` per-gap disposition (Incorporated / Deferred / Dismissed); adopted-rationale requirement for convergence map entries; removed "Optional for all other pipeline runs" (feedback rows 19, 20, 23).
- **Stage 7 CORRECTED/BLOCKED loop** — added explicit Stage 6 return path: CORRECTED and BLOCKED verdicts now route to Stage 6 (Refinement) with re-run requirement; loop until PASS (feedback row 14). Corresponding Rule 16 permitted values updated to include BLOCKED and revised CORRECTED description.
- **Rule 1 Stage specification constraint** — routing statements of any polarity must not appear in stage body outside trigger-feature block (feedback row 21).
- **Part 2 preamble — Minimum-viable rule expression** — fields whose only valid value is `None —` for a given rule must be omitted; padding with obligatory None entries prohibited (feedback row 22).
- **Lightweight variant** — embedded 4-item coherence check inline; removed dependency on full Stage 7 spec (feedback row 21).
- **Part 3 scope** — widened from "`/idp-rca` output" to "Any AI output" (feedback row 24).
- **RULE-027 relocated** to CLAUDE.md § Conventions; Rules 17–19 renumbered to 16–18 (RULE-028–030).

v2.6.0 — 2026-05-05: Walkthrough feedback integration — scope statement, Stage 2b, Stage 7, Rules 16–19, CLAUDE.md ceremony gate.
- **Scope statement** — replaced undefined "prompt authoring task" with enumerated 8-item artifact list (feedback row 5).
- **Stage 2b (Prior Art & Convergence Check)** — new stage in Part 1 pipeline, required before Stage 3 for governance artifacts; produces convergence map + simplification candidates + gaps. `Enforced by: RULE-030.` (feedback row 12)
- **Stage 7 (Whole-Output Coherence Review)** — new final stage in Part 1 pipeline; 4 sub-checks (section order, internal consistency, cross-reference completeness, document-type fit); PASS/CORRECTED/BLOCKED verdicts; required for full pipeline and durable lightweight outputs. `Enforced by: RULE-028.` (feedback row 10)
- **Rule 16 (RULE-028)** — Stage 7 obligation (renumbered from Rule 17; RULE-027 relocated to CLAUDE.md).
- **Rule 17 (RULE-029)** — Scope classification decision procedure (renumbered from Rule 18).
- **Rule 18 (RULE-030)** — Prior art evidence for governance artifacts (renumbered from Rule 19).
- **CLAUDE.md plan completion ceremony** — added self-compliance gate: governance documents must satisfy every rule in their body before marking IMPLEMENTED; open-ended deferrals require a backlog ID and deferral condition. (feedback rows 1, 3, 4)
- **Quick-Reference Checklist** — added rows for Rules 16–19, Stage 2b, and Stage 7.
- **T5.35 retrofit** — all 28 existing rule sections (RULE-001 through RULE-026, RULE-P01, RULE-P02) retrofitted with `Prerequisites:`, `Changes summary:`, and `Pipeline evidence:` fields.
- **Conversion table** — RULE-027 through RULE-030 added to `rule-id-conversion.md`.

v2.5.0 — 2026-05-04: Packages E and F — Pipeline-Bypass Detection + First-Time-Reader Gate + CLAUDE.md enforcement gate.
- **Rule 14 (RULE-025)** — Pipeline-bypass detection: every section heading containing a stable-ID token must carry a `Pipeline evidence:` field. Closes T5.21. Source: full 6-stage pipeline, Package E.
- **Rule 15 (RULE-026)** — First-time-reader gate: every section heading containing a stable-ID token must carry `Prerequisites:` and `Changes summary:` fields. Closes T5.24. Source: same pipeline.
- **CLAUDE.md `## Development Rules`** — Added Instruction-document gate (RULE-023): confirms `Enforced by:` field presence when behavioral rules are added or modified. Closes T5.28.
- Quick-Reference Checklist and scope boundary updated for Rules 14 and 15.

v2.4.0 — 2026-05-04: Packages C and D — Enforcement Location Rule + Trigger Vocabulary Disambiguation Standard.
- **Rule 12 (RULE-023)** — Enforcement location for unconditional obligations: every unconditional behavioral obligation must carry an `Enforced by:` field naming the structural gate that fires it. Source: walkthrough regression RCA step4-bypass-L3-001 (2026-05-03).
- **Rule 13 (RULE-024)** — Trigger vocabulary disambiguation: every step in a multi-step instruction document must carry a `Closed synonym list:` field, and each collision pair must carry a `Precedence:` field. Source: walkthrough regression RCA step4-bypass-L3-003 (2026-05-03).
- Quick-Reference Checklist updated with rows for Rules 12 and 13.
- Scope boundary callout updated to include RULE-023 and RULE-024 in authoring-scope range.

v2.3.1 — 2026-05-04: Package B structural rework — bare-subject retrofit, scope declarations, trigger features, synthesis audit.
- **Rules 2–8 retrofitted to bare-subject transformer form** — each opens with `Every <bare noun phrase> must...` and includes a permitted-value list with `None — <reason>` absence case. Former conditional/property-claim openers ("When...", "If...", "A rule...") rewritten.
- **Scope declarations added to all 24 rules and Part 1 structures** — `> **Scope:** [Authoring | Output | Process]` immediately after each rule heading. Authoring: RULE-001 through RULE-012, RULE-020 through RULE-022. Output: RULE-013 through RULE-019. Process: RULE-P01, RULE-P02.
- **Trigger features + Borderline cases added** to all rules previously missing them (Rules 2–8 via rewrite; Rules 5.1, 5.2, 6.1, 7.1, 9, 10, 11, RULE-P01, RULE-P02 via insertion). All rules now satisfy Rule 1.1 (RULE-002).
- **Synthesis audit** confirmed no merge or split candidates — documented in Part 2 preamble; preamble "retrofit deferral" note updated to mark retrofit complete.
- **clean.md fixture** corrected: pseudo-transformer `"Every plan step that modifies shared state must include..."` rewritten to bare-subject form.

v2.3.0 — 2026-05-04: Walkthrough Round 3 — bare-subject + permitted-values rewrite. Round 3 walkthrough on the v2.2.0 implementation surfaced that "Every X *that does Y* must contain Z" still embeds a classification step in the subject — the same H40-vulnerable layer the transformer form was meant to eliminate. v2.3.0 patches:
- **Rule 1 extension rewritten** — explicit "bare noun phrase" subject requirement; qualifiers move to permitted-value lists; `None — <reason>` for absence cases. Rule 1 example replaced with a worked transformer / pseudo-transformer / self-monitoring contrast.
- **Rules 1.1, 5.1, 5.2, 6.1, 7.1, 9, 10, 11 rewritten with bare subjects** — each now reads "Every rule statement must contain a `<Field>:` field" with permitted values including a `None — <reason>` entry. The qualifier formerly in the subject is absorbed by the permitted-value list.
- **Part 1 §Cross-stage handoff and §Adversarial sequestration rewritten with bare subjects** — handoff anchors on "Every stage output specification"; sequestration anchors on "Every pipeline INPUT block".
- **Self-check lines updated** on all v2.1/v2.2 sub-rules to anchor on bare-subject + permitted-value pattern.
- **Part 2 preamble** documents the bare-subject requirement scope: hard requirement for v2.1+ patches; Rules 1–8 in their current form predate the requirement and are deferred to the v2.1 retrofit backlog item.

v2.2.0 — 2026-05-04: Walkthrough Round 2 — transformer-form rewrite. Round 2 of the walkthrough on the v2.1.0 implementation identified that every new rule was authored in conditional/property-claim shape rather than transformer/authoring-instruction shape — the same Rule 1 weakness the rules were meant to prevent. v2.2.0 patches:
- **Rule 1 extension** — added the transformer-vs-conditional axis with surface-feature authoring test. Format rules now distinguish transformer form (subject is a surface feature, fires on the authoring act) from conditional form (subject is an artifact category, fires on a property check); transformer is preferred.
- **Rules 1.1, 5.1, 5.2, 6.1, 7.1, 9, 10, 11 rewritten as transformer rules** — each subject now anchors on a grep-able surface token pattern; bodies state the required output element directly.
- **Part 1 §Cross-stage handoff and §Adversarial sequestration rewritten as transformer rules** — handoff anchors on Stage N output specifications listing fields consumed by Stage N+1; sequestration anchors on a `Sequestered:` line in generation-stage INPUT blocks.
- **Rule 11 — every Rule N section ends with a `Self-check:` line** — the structural format-rule expression of self-application; replaces the v2.1 implicit-marker convention. Self-check lines added to Rules 1–11 and Part 1 subsections.
- **Part 3 catch-alls rewritten** — surface-feature triggers replace counterfactual self-monitoring tests; each catch-all gains a worked example.
- **Linter vocabulary** — synonym-drift terms (`evidently`, `plainly`, `manifestly`, `self-evidently`) moved to a labeled "high-precision rule-text-only" subsection with documented precision/recall trade-off; deferred to v1.1 linter refinements backlog item.
- **Quick-Reference Checklist** — grouped by Part (Pipeline / Rule shape / Sub-clauses / Honest-framing / Authoring conventions); added transformer-shape row and Self-check row.

v2.1.0 — 2026-05-04: Pipeline-test feedback integration (plan `rule-design-standards-pipeline-feedback.md`). Twelve patches landed:
- **Rule 1.1** — class-of-utterance trigger test + ≥2 worked borderline cases (D1)
- **Rule 5.1** — quota rules require "none at threshold" exit or conditional reformulation (D2)
- **Rule 5.2** — multi-field templates require "minimal — [reason]" brevity allowance (D8)
- **Rule 6.1** — falsifiable test conditions require threshold + horizon + named evaluator + reproducibility test (D10)
- **Rule 7.1** — procedural-constraint rules require uniform applicability or development-context override (D11)
- **Rule 9** (new) — procedural commands require operational definitions (trigger + steps + discrete output) (D4)
- **Rule 10** (new) — pipeline-stage applicability must be specified (uniform or per-stage) (D5)
- **Rule 11** (new) + Part 2 preamble meta-clause — rules apply to their own statements (D12)
- **Part 1 §Cross-stage handoff structure** (new) — handoffs specified as named fields, not implicit prose (D6)
- **Part 1 §Adversarial sequestration** (new) — candidate solutions sequestered from generation stages (D9)
- **Part 3** — added "Positive replacement form" column to all three tables; populated catch-all rows (D3)
- **Part 3 §Compliance theater** (new) — fourth honest-framing table for structural failures that pass phrase-level checks (D7)
- **Quick-Reference Checklist** — one row per new rule and extended sub-clause (D14)

Numbering: existing Rules 1–8 unchanged (preserves 169 external citations counted via `grep -rEn "Rule [1-9]"` on 2026-05-04). New rules append as 9–11. Self-application principle named in Part 2 preamble for conceptual placement near Rule 1.

v2.0.0 — 2026-04-29: Merged Auto-Expert Prompt Building Guide (pipeline design, Part 1) into Rule Design Standards (instruction quality, Rules 1–8). Motivation prose moved to `docs/reference/prompt-authoring-background.md`. Added Part 1 (6-stage pipeline with required output shapes, lightweight variant, control levers), Quick-Reference Checklist, and expanded Relationship table. Rules 1–8 content and numbering unchanged. Retitled from "Rule Design Standards" to "Prompt Authoring Guide."

v1.1.0 — 2026-04-27: Add Rule 8 (investigation-concluding outputs require epistemic markers). Six format-rule sub-requirements: hypothesis preamble, inline claim tags ([Verified]/[Hypothesis]), per-component defect hypothesis, Tools used: footer, absence enumeration, evidence scope. Closes gaps identified in `/idp-rca` plan Rule-Design Guide Audit.

v1.0.0 — 2026-04-25: Initial version. Seven rules establishing format-over-self-monitoring preference, behavior-not-medium scope, and certainty-bias auditing for persistent artifacts.
