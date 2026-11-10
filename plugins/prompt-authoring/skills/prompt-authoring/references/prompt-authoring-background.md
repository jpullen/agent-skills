# Prompt Authoring Background

> This document explains the reasoning behind [`rule-design-standards.md`](rule-design-standards.md) (the Prompt Authoring Guide). Read this for context; follow the guide for instructions.

---

## Executive Summary

This document is the human-facing companion to [`rule-design-standards.md`](rule-design-standards.md). The guide holds format obligations only; rationale lives here to prevent salience competition when Claude reads the guide during authoring tasks. The intended audience is humans designing, reviewing, or extending instruction-authoring rules — not Claude during live authoring.

**Navigate by problem:** § The Core Problem introduces the two failure modes the system addresses. § Part 1 Rationale explains the 6-stage pipeline (eight failure modes, cross-stage handoffs, adversarial sequestration). § Part 2 Rationale explains the instruction quality rules (RULE-001 through RULE-026). Named topic sections explain thematic additions: § Multi-Deployment-Target Guidance Rationale (RULE-031 / Rule 19, three-target taxonomy), § Pipeline Naming Convention Rationale (`[PIPELINE-NNN]` IDs, registry table), § Pipeline Integrity Gates Rationale (RULE-025, RULE-026), § Enforcement and Disambiguation Rationale (RULE-023, RULE-024), § Bare-Subject Transformer Form Rationale (v2.3 bare-noun-phrase subjects), § Transformer/Conditional Axis and Self-Check Rationale (v2.2 additions), § Trigger Quality and Operational Definitions Rationale (v2.1 additions), § Prior Art Convergence, Stage 7, and Companion Document Rationale (v2.6 additions). § Pedagogical Contrasts shows wrong-form examples. § Design Decisions records structural choices. § Provenance records sources and adaptation notes.

---

## The Core Problem

LLMs have broad latent expertise but no built-in mechanism to activate the right parts at the right time. Left unstructured, they produce smart-sounding but generic, averaged reasoning — blending across domains rather than going deep in the right ones.

Two distinct failure modes compound this:

1. **Shallow reasoning** — unstructured prompts let the model jump from input to output in one step, compressing framing, analysis, synthesis, and critique into a single response. Hidden errors accumulate invisibly, and the answer is undebuggable when wrong.

2. **Ignored instructions** — rules that read well but fail under context pressure. The H40 problem: meta-awareness without prevention. An LLM can know a rule exists and still violate it when the context window is saturated or salience competition is high.

The guide addresses both: Part 1 (the pipeline) solves shallow reasoning; Part 2 (the instruction quality rules) solves ignored instructions. Neither alone is sufficient.

The fundamental shift the guide enables: from **prompting** (ask a question, get an answer) to **orchestration** (design a thinking process and run it).

---

## Part 1 Rationale: Why the Pipeline?

Eight failure modes the 6-stage pipeline addresses:

### 1. "Smart but Generic" Answers

LLMs blend across domains when a problem isn't clearly framed, producing answers that sound competent but lack depth or specificity. The model averages over its training rather than focusing on the particular problem.

**Stage 1 (Framing)** forces explicit problem definition before any reasoning begins — goals, constraints, assumptions, and unknowns are named before analysis starts. This converts a vague query into a structured problem with a verifiable scope.

### 2. Brittle Role Prompting

Prompts like "You are a cardiologist" work for narrow problems but are overly rigid, prone to overconfidence within the role, and poorly suited for multi-domain problems that require combining perspectives.

**Stage 2 (Expertise Routing)** shifts from role assignment to explicit domain selection. The model identifies 3–6 relevant domains, states why each is needed, and describes what each contributes. Multiple perspectives can be combined dynamically rather than collapsed into a single role's worldview.

### 3. Compressed Reasoning

Most prompting compresses four distinct cognitive acts — understand, analyze, decide, justify — into a single step. This creates hidden errors: the model may frame the problem poorly, pick the wrong lens, reach a weak conclusion, and justify it fluently, and the output gives no indication which step failed.

**Stages 1–6** decompose reasoning into inspectable stages. Each stage has an explicit input/output contract. This mirrors how strong human reasoning actually works and makes each step more reliable.

### 4. Explanation Quality vs. Decision Quality

LLMs are better at explaining things than at prioritizing tradeoffs, making clear decisions, and aligning with specific constraints. Outputs tend to be informative but non-committal — they describe the problem without recommending a path.

**Stage 4 (Synthesis & Decision)** explicitly requires a recommendation with reasoning and stated assumptions. The output format — Recommendation / Reasoning / Assumptions — shifts the deliverable from "informative" to decision-grade. The model cannot produce an explanation that avoids taking a position.

### 5. Hidden Blind Spots

Standard outputs tend to hide uncertainty, skip edge cases, and avoid adversarial thinking. The model follows the natural path to a conclusion without testing it.

**Stage 5 (Adversarial Critique)** is structurally required — the model cannot skip directly from decision to refinement. Weaknesses, challenged assumptions, risks, and counterarguments must be produced before the recommendation can be refined. This reduces overconfidence and surfaces failure modes that the synthesis step missed.

### 6. Incoherent Multi-Domain Mixing

Real problems are rarely single-domain. Without structure, the model may pick the wrong primary lens or mix domains incoherently — applying a financial framework where an organizational design framework was needed, or layering insights without synthesizing them.

**Stages 2–3** enforce explicit domain selection and coordinated multi-lens analysis. Each domain contributes its insights, risks, and tradeoffs before they are synthesized in Stage 4. The synthesis step operates on a structured input rather than mixing domains ad hoc.

### 7. Undebuggable Errors

In a single-step prompt, if the answer is wrong, there is no inspection point. The reasoning is compressed inside a single response and the failure mechanism is opaque.

With the pipeline, each stage is an inspection point: bad framing → fix Stage 1; wrong expertise → fix Stage 2; weak analysis → fix Stage 3; poor decision logic → fix Stage 4. The process is inspectable, improvable, and the failure is localizable.

### 8. Prompting → Orchestration Mindset

The deepest motivation is a shift in how LLMs are used:

- **Basic use:** ask a question, get an answer — the model's default path
- **Advanced use:** design a thinking process and run it — the model as a reasoning pipeline

The pipeline turns the LLM into a structured reasoning system with distinct components rather than a one-shot responder. The author's job is not to write a good question but to architect a good process.

---

## Part 1 Usage Notes

**Stage chaining:** Each stage feeds the next. Paste the previous stage's output as the `INPUT` block for the next stage. The chain breaks if a stage's required output shape is incomplete — fix the current stage before proceeding.

**Full vs. lightweight selection:** Use the **Full Pipeline (`[PIPELINE-001]`)** when Stage 2 identifies ≥3 relevant domains, when output will be acted on without human review, or when the task scope spans multiple sections of the Relationship table. Use the **Lightweight Pipeline (`[PIPELINE-002]`)** otherwise. When in doubt, start with the Lightweight Pipeline and escalate to the Full Pipeline if Stage 2 returns ≥3 domains.

**Model tier guidance:** For the Full Pipeline (`[PIPELINE-001]`), default to sonnet. Escalate to opus when Stage 2 returns ≥5 domains or when the cause tree produces multiple concurrent branches with competing frameworks. For the Lightweight Pipeline (`[PIPELINE-002]`), haiku or sonnet is sufficient. **Per-target note:** on Claude Chat, model tier is fixed at session start; mid-pipeline escalation requires session restart. Cross-reference: `CLAUDE.md` model tier table (Haiku/Sonnet/Opus with observable task properties), `model-guidance.md` (advisor-session model selection, extended thinking guidance).

**Priorities block (Stage 3):** Leave blank if you have no strong priority constraints — the model will surface tradeoffs and ask. Fill it in if you know a constraint in advance (e.g., "minimize time-to-decision over solution completeness").

---

## Part 2 Rationale: Why the Instruction Quality Rules?

### The H40 Problem

H40 is "meta-awareness without prevention" — the observation that an AI can be aware of a failure mode and still produce the failure under pressure. Defined in `docs/design/golem-design.md` §18.1 with supporting research: if-then triggers outperform awareness-only approaches (Gollwitzer 1999 implementation intentions, human behavioral science; applied to LLMs by structural analogy — direct LLM equivalents unmeasured).

The implication for instruction authoring: rules that say "be aware of X" or "remember to do Y" fail under context pressure. Rules that say "when producing output Y, the output must have shape Z" succeed — because the trigger is the output act itself, not internal metacognition.

This is the core distinction between format rules and self-monitoring rules ([RULE-001] / Rule 1). It is not a stylistic preference — it reflects a known constraint in how LLM behavior is shaped.

### Three-Tier Enforcement Model

The instruction quality rules govern only the documentation tier. The full hierarchy (from `docs/reference/project-anti-patterns.md`):

1. **Hooks** — execute unconditionally in the harness; don't require AI compliance
2. **Skills** — invoked explicitly; AI must choose to call them
3. **Tests** — catch violations after the fact
4. **Documentation** — what Claude reads; weakest tier; where Rules 1–8 apply

Rule Design Standards [RULE-001] through [RULE-004] / Rules 1–3 make the documentation tier as strong as possible within its constraints. When documentation-tier rules fail repeatedly, that is a signal to move enforcement up a tier — not to add more documentation.

### Why [RULE-001], [RULE-003], [RULE-004] / Rules 1–3 Form the Core

Rules 1–3 form a unit: prefer format rules ([RULE-001] / Rule 1), put them first ([RULE-003] / Rule 2), keep them concrete ([RULE-004] / Rule 3). Together they address the most common failure mode: rules that get added to CLAUDE.md, sound good, and change nothing.

The practical distinction: a format rule fails visibly — the output doesn't have the required shape, and a reader can see the violation. A self-monitoring rule fails invisibly — the model processed the content normally and nothing in the output reveals the gap. Invisible failures don't get fixed; visible failures do.

### Why [RULE-005] / Rule 4 (Behavior Scope) Matters

Rules scoped to a medium — "in backlog entries," "in responses" — leave the same behavior un-governed everywhere the author didn't enumerate. The rename test catches this at authoring time. A rule about "propagating state changes" that only mentions the roadmap is a rule that leaves the experiment log, backlog, and error catalog unprotected.

### Why [RULE-006] / Rule 5 (Certainty Bias) Matters

Templates are the strongest format rules in practice — they shape every artifact produced with them. A template with only certainty-shaped slots (Bug / Cause / Fix) produces certainty-shaped artifacts regardless of how uncertain the actual situation is. The model fills the slot it is given. This is the mechanism behind most "root cause found" conclusions that later turn out to be hypotheses.

Adding Observed and Hypotheses slots is not about making artifacts longer — it is about making the certainty level visible from the structure, so downstream readers can see whether a conclusion is confirmed or still a candidate.

### Why [RULE-013] / Rule 8 (Epistemic Markers) Matters

Investigation-concluding outputs are the highest-stakes outputs in this project — they propagate downstream as authoritative and inform decisions. [RULE-013] / Rule 8 makes certainty level visible from the output shape alone, without requiring a reader to parse body prose.

The `[Verified]` / `[Hypothesis]` tags are the format rule. The honest-framing vocabulary tables are the catch for cases where the tag was omitted and the phrase itself signals the violation. Together they cover the two ways epistemic failures appear: missing labels and overconfident language.

---

## Multi-Deployment-Target Guidance Rationale

The v2.8.0 additions (companion to `multi-surface-guidance.md`; terminology migrated to "deployment target" in v2.8.1) address a structural gap: the guide implicitly assumed Claude Code infrastructure (file system, hooks, tests, backlog), and several rules cite that infrastructure unconditionally. When the guide is used on a deployment target that lacks the infrastructure, those rules degrade silently — fields point to nothing, authors fill placeholder values, or runs are misclassified to satisfy a gate the deployment target cannot honor.

### Why three deployment targets

The canonical taxonomy is three deployment targets, two of which are inherited from `platform-guide.md`:

| Deployment Target | What it is | Infrastructure |
|---|---|---|
| **Claude Code Local** | Claude Code on CLI, Desktop app, or VS Code (one deployment target; the platform guide's Local row) | Persistent file system, hooks, tests, backlog, plan files, anti-patterns catalog |
| **Claude Code Remote** | Claude Code on Web or Mobile (the platform guide's Remote row) | Session-persistent file system, hooks, tests, backlog (with worktree and concurrency limits per `platform-guide.md`) |
| **Claude Chat** | claude.ai chat interface (no Claude Code; future MCP / custom-connector deployment target) | Session-only memory, uploads only — no hooks, no tests, no backlog, no file system, no `.claude/settings.json` |

Claude Chat is structurally distinct from both Claude Code deployment targets — not a degraded version of Claude Code but a different product. The user authoring an instruction document needs to know at write time which deployment target their rules will fire on; runtime detection (Anthropic's Agent Skills "progressive disclosure" pattern) is a different layer.

### Why "Deployment Target" was chosen over "Surface" (v2.8.1 rename)

The v2.8.0 work inherited the term "surface" from user-stated requirements without challenging it. A retroactive rename test (RULE-005) surfaced that "surface" is metaphorical and lacks established prior art in the relevant taxonomies. "Deployment Target" matches CI/CD vocabulary and accommodates Claude Chat as a future MCP / custom-connector deployment target — which the original "surface" framing did not anticipate. The hard rename in v2.8.1 (no synonym retention) was safe because v2.8.0 had not yet merged to main; no external consumers existed.

### Why infrastructure-dependent rules need per-target declarations

A rule that says `Enforced by: hook <name>` reads as binding on every deployment target. On Claude Chat, hooks don't exist — the obligation has the same enforcement weight as documentation. Without an explicit per-target declaration, the rule's strength is invisible. RULE-031 makes the deployment-target dependency surface-verifiable: every infrastructure-citing rule declares which permitted values apply on which deployment target.

The collapse pattern is consistent. On Claude Chat:
- **RULE-011** (pre-promotion compliance scan) — no file system to scan; manual author responsibility limited to material in conversation context.
- **RULE-023** (`Enforced by:`) — no hook / test / backlog; only `Not enforceable on this deployment target — manual author responsibility` is permitted.
- **RULE-025** (`Pipeline evidence:`) — no `docs/plans/` paths; new permitted value `Pipeline evidence: Claude Chat session — <date or topic>` is canonical.
- **Stage 7c** (cross-reference completeness) — verification limited to material in conversation context; record `[7c limited: file paths unverifiable on this deployment target]` alongside the verdict.
- **Part 3 fabrication `[PA]` row** — anti-patterns catalog inaccessible; permitted form is `suspected pattern (anti-patterns catalog not accessible on this deployment target)`.

The collapse is consistent because the underlying cause is consistent: Claude Chat lacks the upper three tiers (hooks > skills > tests) of the three-tier enforcement model. Documentation is the only tier available, and documentation is the H40-vulnerable tier the guide was written to harden. On Claude Chat, the guide's enforcement strength reduces to author discipline plus the deployment target's own narrower context profile.

### Where Claude Chat is structurally stronger

Claude Chat has narrower, more focused context than a Claude Code session that may accumulate dozens of tool invocations and file edits. For short-to-medium pipeline runs, the cleaner context profile is a mild advantage — lower probability that pipeline rules lose salience to competing tool output. Additionally, Claude Chat has no file-mutation capability, so a partially-executed pipeline cannot silently commit malformed artifacts to a repository. Honest framing requires both directions: the deployment target loses infrastructure-dependent enforcement but gains narrower context and zero commit-risk.

### Why the misclassification authoring test on RULE-025 matters

Without an explicit Chat-specific permitted value, authors running the Full Pipeline on Claude Chat will reflexively select the lightweight fallback (`Pipeline evidence: lightweight variant — <reason>`) because the file-path form is structurally unavailable. That records a Full Pipeline run as a Lightweight Pipeline run in the artifact's own pipeline evidence, producing a systematic misclassification that defeats the gate. The new `Claude Chat session — <date or topic>` permitted value plus the authoring test (`if you ran 6+ stages, you ran Full Pipeline; do not select the lightweight permitted value to satisfy this gate`) close that path.

### Why output-scope rules are exempt

RULE-013 through RULE-019 (epistemic markers, hypothesis preamble, inline claim tags, per-component defect hypothesis, tools used: footer, absence enumeration, evidence scope) govern tokens emitted in causal claims. The H40 dynamics they prevent (context-pressure dropouts of marker requirements) operate identically on every deployment target — context pressure is a property of long output sequences, not of the host deployment target. RULE-031 explicitly declares those rules `Applies uniformly across deployment targets` so authors don't add per-target tables that wouldn't change anything.

---

## Pipeline Naming Convention Rationale

The v2.8.0 additions also introduce stable pipeline identifiers (`[PIPELINE-001]`, `[PIPELINE-002]`) and a Pipeline Registry section in Part 1. Prior to v2.8.0, the guide's two pipelines were referred to descriptively ("the full pipeline," "the lightweight variant") with no stable identifiers. RULE-028, RULE-030, and RULE-021 each cited "the pipeline" or "the full pipeline" — citations that resolved correctly in a two-pipeline corpus but would not scale.

### Why stable pipeline IDs

External practice is uniform on this point. Reducto, n8n, AWS Data Pipeline, Pulumi Harness, and GitLab CI all use stable identifiers as the primary handle for pipelines (`Reducto Pipeline ID`, `n8n Workflow ID`, `df-NNN` for AWS Data Pipeline, named pipelines as registry primitives in Pulumi). Stability matters because the ID outlives version changes — a redeploy may update what the pipeline does, but the ID continues to point to the same logical entity.

Our `[PIPELINE-NNN]` form parallels the existing in-corpus ID conventions (`RULE-NNN`, `RULE-P0N`, `T5.NN`, `[ERR-NNN]`). The bracketed prefix integrates into the RULE-025 / RULE-026 trigger feature lists with one entry per rule.

### Why a registry table

n8n's Workflow ID documentation lists every workflow's ID alongside its canonical name and trigger conditions. Pulumi's pipeline-package Pulumi Registry uses the same pattern. Externalizing the pipeline list as a registry table satisfies two constraints: a first-time reader can navigate the corpus by ID; future pipeline additions append rows rather than threading new prose through the existing Part 1 narrative.

### Why "Lightweight Variant" was renamed to "Lightweight Pipeline"

The original name framed the lightweight form as a subordinate variant of the full form. With both pipelines now first-class registry entries, the variant framing is incorrect. The closed synonym list (RULE-024) preserves the old name as a deprecated synonym for citation backward compatibility but routes new references to the canonical name.

### Adding a new pipeline definition

Adding a third or fourth pipeline (e.g., a meta-pipeline, a benchmark-specific pipeline, an integration pipeline) is itself a governance-artifact change requiring Stage 2b prior art and Stage 7 coherence review under `[PIPELINE-001]`. The Pipeline Registry table records the addition; the new pipeline's heading carries a `[PIPELINE-NNN]` token that fires RULE-025 / RULE-026.

---

## Pipeline Integrity Gates Rationale

The v2.5.0 patches (companion to Package E of `rule-design-standards-coherence-rework.md`) add two rules that address a structural gap identified during the T5.16 triple-loop (2026-05-02): design decisions in ID-bearing sections could not be verified — from the artifact alone — as pipeline-compliant or pipeline-bypassed.

### Why [RULE-025] / Rule 14 (Pipeline-Bypass Detection)

Design decisions documented in sections with stable RULE-NNN IDs carry an implicit claim: they were authored with sufficient rigor to warrant a permanent identifier. But the artifact alone cannot confirm whether the decision passed through Stage 5 adversarial critique or was generated in a single pass. Without this confirmation, the stable-ID scheme silently inflates — it becomes a formatting convention rather than a quality signal.

Rule 14 makes pipeline compliance checkable from the artifact: every ID-bearing section must name the plan document containing the pipeline transcript (`Pipeline evidence:` field). If no such document exists, the rule forces the author to either run the pipeline or refrain from assigning a stable ID. The None exit (`None — heading does not contain a stable-ID token`) is the structural escape for non-ID-bearing content, so the rule fires only where the implicit quality claim actually exists.

Self-application is mandatory: [RULE-025] itself is an ID-bearing section and must name its own pipeline evidence. This creates a chicken-and-egg situation resolved by citing the plan file that commissioned the pipeline run — making the self-application concrete rather than aspirational.

### Why [RULE-026] / Rule 15 (First-Time-Reader Gate)

Accumulated patch content — the v2.1/v2.2/v2.3/v2.4/v2.5 progression in this guide — is navigable only by participants present for each round. A first-time reader has no orientation: they cannot tell what background is assumed, what version introduced which behavior, or where to start. This is not a documentation-quality problem; it is a structural one. The information does not exist in the artifact's current form.

Rule 15 addresses this with two mandatory fields in every ID-bearing section: `Prerequisites:` names the background a reader must have before the section makes sense; `Changes summary:` identifies what the section introduces relative to prior versions. Together these fields convert an expert-context document into one a reader can enter from any section.

The rule shares its trigger surface with [RULE-025] / Rule 14 (heading containing a stable-ID token), making the two rules a paired gate: Rule 14 audits pipeline lineage; Rule 15 audits reader accessibility. Both fire unconditionally on ID-bearing sections, and both use the same None exit for sections without stable IDs.

---

## Enforcement and Disambiguation Rationale

The v2.4.0 patches (companion to Packages C and D of rule-design-standards-coherence-rework.md) add two rules surfaced by the walkthrough regression RCA 2026-05-03. Both address failure modes that operate below the H40 level: not "Claude knows but ignores the rule" but "Claude follows the rule — but the rule has no structural backing."

### Why [RULE-023] / Rule 12 (Enforcement Location)

Documentation-tier rules are the weakest enforcement tier (see § Three-Tier Enforcement Model). A rule that states an unconditional behavioral obligation but names no structural gate is a claim without a mechanism: the obligation sounds firm, but the backing is the same as any other documentation. Under context pressure, undifferentiated documentation is the first thing that degrades.

The walkthrough regression RCA (`step4-bypass-L3-001`) identified a concrete instance: an existing obligation was stated unconditionally in CLAUDE.md with no hook, test, or skill to catch violations. The instruction was technically compliant (correctly formatted) but structurally unbacked.

Rule 12 requires every unconditional behavioral obligation to carry an `Enforced by:` field that names the gate: hook name, test file, or skill invocation point. When no structural gate exists, the required value is `Documentation-tier only — backlog: <ID>` — which converts a latent compliance gap into a visible, tracked debt item. This is the mechanism that distinguishes "unconditional in documentation" from "unconditionally enforced."

The three-tier enforcement model existed before this rule. Rule 12 makes it operational: every obligation must state which tier backs it, and if the answer is "documentation only," the backlog item is mandatory.

### Why [RULE-024] / Rule 13 (Trigger Vocabulary Disambiguation)

Multi-step skills developed iteratively accumulate synonym drift. An early step claims a trigger vocabulary; later steps add synonymous terms. When the AI encounters an input matching multiple triggers, it has no resolution criterion and defaults to whichever trigger was most recently reinforced — which is arbitrary from the instruction author's perspective.

The walkthrough regression RCA (`step4-bypass-L3-003`) identified this as the root cause of bypass failures in the `/walkthrough` skill: two steps each had trigger language that matched the same class of user input, with no precedence rule. The model alternated between steps depending on recency effects rather than intent.

Rule 13 makes disambiguation a structural requirement at authoring time. The `Closed synonym list:` field forces the author to enumerate exclusive trigger sets per step — making overlap detectable by reading adjacent steps. The `Precedence:` declaration resolves conflicts that survive the enumeration pass: "Step N takes precedence when both triggers fire and [observable condition]." The worked example (walkthrough Step 4a vs. Step 5) demonstrates the pattern concretely — a reader can see exactly what "closed synonym list" and "precedence declaration" mean in a real multi-step skill, without having to infer the pattern from abstract description.

---

## Bare-Subject Transformer Form Rationale

The v2.3.0 patches address a deeper version of the transformer-form bug surfaced in Round 2. v2.2 rewrote rule subjects from conditional ("when X holds, the artifact must Y") to apparent transformer form ("every X *that does Y* must contain Z"). But the qualifier embedded in the subject — *"that does Y"* — still requires the author to classify their artifact before the rule fires. The classification step is the H40-vulnerable layer the transformer form was meant to eliminate.

### Why bare-noun-phrase subjects

A subject with a relative clause (`every plan step that modifies shared state`), a participle (`every rule containing imperative verbs`), or a conditional embedded in the subject is a pseudo-transformer: the rule fires only after the author classifies their artifact. The user-surfaced example was *"every plan step **that modifies shared state** must contain a `Propagate to:` bullet"* — corrected to *"every plan step must contain a `Propagate to:` bullet, value can be `None`."* The corrected form fires unconditionally on every plan step; the qualifier (modifies-shared-state) becomes a permitted value of the bullet's content rather than a precondition for the rule firing.

### Why qualifiers move to permitted-value lists

[RULE-007] / Rule 5.1's "None at threshold" pattern was already the right shape — a quota with an explicit "no items at threshold" exit value. Round 3 generalized that pattern across all v2.1/v2.2 sub-rules: each rule fires unconditionally on every rule statement, with the qualifier-formerly-in-subject absorbed by a `None — <reason>` entry in the field's permitted-value list. The cost is verbosity (every rule body now references multiple fields, most as `None — N/A`); the benefit is unconditional triggering with no classification step.

### Why Rules 1–8 were initially deferred (resolved v2.3.1)

Rules 1–8 in their original form predated the bare-subject requirement. Rewriting them during the v2.3.0 session would have doubled the patch scope and risked degrading flow further. The Part 2 preamble named the deferral explicitly; retrofit was tracked in the v2.1 retrofit backlog item alongside the CLAUDE.md / SKILL.md retrofit work.

**Resolution (v2.3.1):** The retrofit was completed in Package B of the coherence-rework plan (2026-05-04). Rules 2–8 were rewritten to bare-subject transformer form; scope declarations, trigger features, and borderline cases added to all rules; synthesis audit confirmed no merge or split candidates. The Part 2 preamble now reads "retrofit complete v2.3.1." No outstanding deferral remains from the original v2.3.0 deferral.

### Why a per-rule field requirement instead of a per-rule footer

Considered alternatives: (a) every rule body shows all 8 fields explicitly with `None — N/A` entries; (b) a single matrix at the end of Part 2 listing fields × rules. Option (a) bloats the doc; option (b) decouples the structural requirement from the rule's prose. v2.3 takes a middle path: each sub-rule (1.1, 5.1, etc.) defines one field with permitted values; the field name appears in the sub-rule's body; rules elsewhere implicitly use `None — <reason>` for fields where they don't substantively apply. This matches v2.1's `Self-check:` pattern (each rule has one) without requiring per-rule field tables.

### Pedagogical Contrasts

The Claude-facing guide shows only the canonical right form for each rule (per the two-file design decision: guide = format obligations only). Contrast pairs — wrong forms with explanation of why they fail — live here so they're available to humans designing or reviewing rules without creating salience competition for the AI during authoring tasks.

**[RULE-001] / Rule 1 (transformer rule shape).**

| Form | Example | Why it fails |
|---|---|---|
| Transformer (strong) | *"Every plan step must contain a `Propagate to:` bullet. Permitted values: list of downstream artifacts to update, or `None — no shared state modified by this step`."* | Canonical. |
| Pseudo-transformer | *"Every plan step that modifies shared state must include a `Propagate to:` bullet."* | The qualifier `that modifies shared state` is a conditional embedded in the subject. The author has to classify their plan step before the rule fires — the same H40-vulnerable layer the transformer form was meant to eliminate. |
| Self-monitoring | *"Commit propagation inline — do not defer."* | No observable trigger. The rule fires when the AI notices it should propagate, which is metacognitive. |

**[RULE-004] / Rule 3 (narrow and concrete).**

| Form | Example | Why it fails |
|---|---|---|
| Strong | *"Start with a one-line hypothesis."* | Canonical. Surface check: count the lines before the first non-hypothesis content. |
| Weak | *"Think carefully before responding."* | Cannot be verified by reading the output. "Think carefully" describes an internal state, not a structural requirement. |

**[RULE-020] / Rule 9 (procedural commands).**

| Form | Example | Why it fails |
|---|---|---|
| Operational (strong) | *Trigger:* `[Verified]` count = 0 in a causal-claim section. *Steps:* (1) re-check tokens; (2) attempt marker; (3) write `Stipulation:` if none. *Output:* revised output with marker, or `Stipulation: <reason>` line. | Canonical. Trigger / Steps / Output blocks all surface-checkable. |
| Aspirational (weak) | *"Halt and reconsider before publishing claims without sources."* | No Trigger block (when does this fire?), no Steps (what does "reconsider" mean operationally?), no Output (what does completion produce?). Reader cannot confirm execution from the artifact. |

**Why the guide doesn't show these contrasts inline.** The Claude-facing guide is read during authoring tasks. Counter-examples in the guide create salience competition: the wrong form sits in the same context window as the right form, and the model may pattern-match either. The two-file design decision (v2.0.0) split format obligations (guide) from rationale (this document) precisely to keep the guide's authoring context clean of wrong forms. Part 3's banned-phrase tables in the guide are an exception — they're operational vocabulary the AI scans against its own output, not pedagogical contrasts shown during authoring.

---

## Transformer/Conditional Axis and Self-Check Rationale

The v2.2.0 patches surfaced from the Round 2 walkthrough of the v2.1.0 implementation. The walkthrough identified one dominant pattern — *every new rule was conditional/property-claim shape rather than transformer/authoring-instruction shape* — and several derivative cleanups.

### Why the transformer/conditional axis ([RULE-001] / Rule 1 extension)

[RULE-001] / Rule 1 originally distinguished format rules (output shape) from self-monitoring rules (metacognition). Both transformer rules and conditional rules can be format rules in that sense — both verifiable from output. The missing axis is *what fires the rule*: the act of authoring (transformer) vs. an artifact-property check after authoring (conditional). Without this distinction, "format rule" admits both shapes and the conditional form is the path of less resistance — generation-mode defaults to property-claims because that is the natural shape of describing artifacts.

The transformer/conditional axis makes the distinction first-class. Rules whose subjects contain a surface-feature trigger (a verb, a digit, a token pattern) can be transformer-shaped: "Every X must contain Y." Rules whose subjects describe artifact categories ("rules that govern …") inherit the conditional weakness — they require the author to first classify their artifact before the rule engages, and the classification step is H40-vulnerable.

### Why every Rule section ends with `Self-check:`

v2.1's [RULE-022] / Rule 11 named the self-application principle but left the implementation to the author. The principle then went unimplemented across the v2.1 patches themselves — mechanism claims appeared without markers, conditional rules appeared without Rule 1 audits. v2.2's structural reformulation requires every Rule N section to end with a labeled `Self-check:` line stating which earlier rule applies and the surface feature confirming compliance. The line is the format-rule expression of self-application: a reader (and a future linter) can confirm execution from the artifact alone.

### Why Part 3 catch-alls were rewritten with worked examples

v2.1's catch-alls used self-monitoring counterfactual tests ("would the natural replacement be 'try harder'?", "remove the rule mentally — does the output change?"). These were [RULE-001] violations themselves — counterfactual mental simulation rather than surface-feature scans. v2.2 rewrites each catch-all with explicit grep-able trigger features and a worked example showing the trigger fired, the diagnosis applied, and the positive replacement produced.

### Why the linter vocabulary added a high-precision section

The synonym-drift terms (`evidently`, `plainly`, `manifestly`, `self-evidently`) reliably indicate [RULE-013] / Rule 8 violations in rule-text and analytical claims, but produce false positives in narrative prose. Promoting them to the general vocabulary without context filtering would burden every plan, backlog item, and skill description that narrates a past state. The high-precision section retains the entries (so they're scanned and surfaced as evidence) but documents the precision/recall trade-off — formal context filtering is deferred to the existing v1.1 linter refinements backlog item.

### Why the Quick-Reference Checklist was grouped by Part

v2.1 left the checklist as a flat 25-row list — manageable but accumulating. v2.2 groups by Part (Pipeline / Rule shape / Sub-clauses / Honest-framing / Authoring conventions) so reviewers can apply only the sections relevant to their artifact. The grouped form also makes the [RULE-022] / Rule 11 self-application checklist row visible as the structural close-out of the Rule-shape group, rather than buried mid-list.

---

## Trigger Quality and Operational Definitions Rationale

The v2.1.0 patches integrate twelve gaps surfaced by an iterative pipeline-test that produced a "v1.0 → v1.5" delta on a complex prompt authored using the guide. The patches recur at the meta-level: they are gaps in the **guide that produced the prompt**, not idiosyncratic to the specific prompt under test. Each patch is documented below with the failure mechanism it addresses.

### Why [RULE-002] / Rule 1.1 (Class-of-Utterance Trigger Test)

A format rule scoped to a discrete artifact element (a named field, a section header) fires reliably — the AI sees the slot and fills it. A format rule scoped to a class of utterances ("every causal claim," "any output asserting X") requires a recognition step before the format constraint engages: the AI must classify the utterance as in-scope before the rule fires. Under context pressure, the recognition step degrades silently — producing rule-shaped guidance that fails like a self-monitoring rule. The trigger test plus borderline cases give the AI surface-feature anchors that fire without internal classification.

### Why [RULE-007] / Rule 5.1 (Quota Exit Clauses)

Quotas without exits force shape regardless of substance — the same mechanism behind the certainty-shaped Bug/Cause/Fix template that [RULE-006] / Rule 5 already addresses. The "at least N defects per domain" form is a [RULE-006] violation in disguise: the slot must be filled, so it gets filled with whatever shape resembles the slot. Adding "none at threshold" as a valid answer turns the quota into a conditional and lets the AI report absence honestly.

### Why [RULE-008] / Rule 5.2 (Brevity Allowances)

Field-count requirements without brevity allowances are the multi-row analogue of [RULE-007] quota exits: 7 fields × 7 domains = 49 mandatory cells, and any genuinely thin cell becomes padding. The brevity allowance ("minimal — [reason]") is the structural escape hatch — it satisfies the field-count gate while honestly signaling absence-of-detail.

### Why [RULE-010] / Rule 6.1 (Operationalized Falsifiability)

"Falsifiable" without thresholds, horizons, and evaluators is rhetorical falsifiability — the rule sounds testable but cannot be tested. The pipeline-test surfaced concrete numbers (inter-rater agreement <70%, ≥30% splitting, 3-month or 10-output horizon, named evaluators) that turn the rule's success condition into something a third party can run. The reproducibility test ("could a third party run this from the spec alone?") is the cheap check that catches under-operationalized conditions before they ship.

### Why [RULE-012] / Rule 7.1 (Development-Context Override)

Procedural-constraint rules (halts, gates) that are unconditional create a hidden choice for the rule-author: violate the rule to iterate on it, or follow the rule and be unable to test downstream behavior. Authors operating in violation-by-default mode silently erode the rule's authority. The development-context override clause names the override pattern explicitly so iterating on rules doesn't require breaking them.

### Why [RULE-020] / Rule 9 (Procedural Commands Need Operational Definitions)

"Halt and reconsider" looks behavioral but triggers on internal states ("when this seems necessary") — a [RULE-001] violation in disguise. The three-step operational form (trigger / steps / discrete output) converts the command into a format rule: the AI knows what artifact it must produce, and a reader can confirm execution from the output alone.

### Why [RULE-021] / Rule 10 (Pipeline-Stage Applicability)

A rule designed for one pipeline stage misfires at others where its preconditions don't hold. *"Every causal claim needs `[Verified: source]`"* applies at synthesis stages where verification is possible; at framing stages, `[Verified]` is not available because nothing has been verified yet. [RULE-021] / Rule 10 forces the author to specify uniform-or-per-stage applicability before shipping.

### Why [RULE-022] / Rule 11 (Self-Application)

A rule that mandates epistemic markers and itself contains markerless claims has an internal inconsistency that undermines its authority. Self-exempting rules signal aspirational documentation: the author has implicitly classified the rule as too important to govern its own author, which is the same psychological mechanism producing the violations the rule was written to prevent. The Part 2 preamble names self-application as a governing principle so readers encounter it before the numbered rules.

### Why Cross-Stage Handoff Structure ([RULE-P01] / Part 1)

Implicit handoffs ("use stage N's analysis") leave the receiving stage to infer what mattered. Receiving stages either invent missing context or proceed without it — context loss equivalent to lost-in-the-middle effect across the stage boundary. Naming fields explicitly in the producer's output and consumer's TASK block converts the implicit handoff into a structural contract.

### Why Adversarial Sequestration ([RULE-P02] / Part 1)

When a candidate solution is visible during a stage instructed to generate solutions independently, generation converges on the candidate even when the stage is explicitly told to ignore it. The convergence is not a discipline failure — it is a salience effect. Sequestration removes the candidate from generation-stage inputs entirely; that is the only reliable mitigation.

### Why Execution Isolation ([RULE-P03] / Part 1)

RULE-P01 and RULE-P02 are *artifact-shape* rules: they govern what fields appear in the producer's output specification and what content appears in a stage's INPUT block. Neither governs *execution mode* — whether stage N+1 runs in a fresh model context or in the same context that produced stage N's output. The G1 gap named in `critique-of-pipeline-001-evaluate-modular-shell.md` is the consequence: on Claude Code (Local or Remote), a single `Agent`-less invocation can satisfy every RULE-P01 / RULE-P02 obligation at the prompt level while running all stages in one model context, and the model retains full memory of every prior stage's output. The artifact looks compliant; the execution is not isolated.

The mechanism is the same as in *§ 8. Prompting → Orchestration Mindset* (lines 78–84 of this document): when an LLM is used as a single one-shot responder, intermediate reasoning is invisible and unrecoverable. The pipeline turns the LLM into "a structured reasoning system with distinct components" — but only if the components actually run in distinct contexts. Stages that share context share latent state, and per-stage convergence on a single reasoning trajectory follows from that shared state irrespective of the artifact-level sequestration RULE-P02 imposes. Sequestration is necessary (without it, the candidate is visible at the prompt level) but not sufficient (with it, the candidate is still implicitly carried by same-context execution).

The `Execution context:` field converts execution mode into a surface-checkable artifact shape: every stage invocation declares which isolation guarantee the run actually had. The per-target table is a pragmatic compromise. On Claude Code Local and Remote, the Agent tool exists and `Isolated subagent — fresh context` is the canonical default; Remote's one-subagent-at-a-time constraint (per CLAUDE.md § Subagent Execution) is operational, not structural, so the artifact-shape declaration is identical to Local's. On Claude Chat there is no Agent tool and no way to spawn a fresh-context stage; `Sequential same-context — degraded execution` is the only honest declaration, and the rule explicitly downgrades downstream `Decision:` and `Verdict:` fields to advisory rather than pretending the isolation held. The Claude Chat fallback row is the rule being honest about a structural limitation of a deployment target, not a workaround that papers over it.

### Why Critique Grounding ([RULE-P04] / Part 1)

A critique of an internal artifact that contains zero verbatim quotes from the target was generated without source contact. The author worked from prior assumptions about what the artifact says rather than what it actually says, and the resulting critique reinvents constructs the artifact already contains. The G6 failure mode named in `critique-of-pipeline-001-evaluate-modular-shell.md` is the existence proof: a six-stage compiled critique of "PIPELINE-001" recommended retrieval / sequestration / multi-agent deliberation — each of which is already operationalized at a more specific level in the standards document (Stage 2b / RULE-P02 / Adversarial Sequestration) — without quoting a single line of the target.

The `Verbatim quotes:` field converts the failure mode into a surface-checkable artifact shape. A critique that cannot produce three verbatim quotes from a named target either (a) has not read the target, in which case the critique is unfounded; or (b) is operating under RULE-P02 sequestration, in which case the `None — target is sequestered ...` permitted value names the downstream stage where the quotes will appear. The rule pairs with RULE-P02: where RULE-P02 keeps candidate solutions out of generation stages, RULE-P04 keeps critique stages anchored to the target they critique. The two together prevent the symmetric failure modes — generation convergent on visible candidates (mitigated by P02), and critique unmoored from invisible targets (mitigated by P04).

The rule fires on artifact production, not conversational turns. A conversational critique that gets promoted into an artifact (filed to a plan, backlog entry, or design document) gains the obligation at promotion; this matches the broader pipeline pattern of distinguishing ephemeral exploration from durable governance artifacts.

### Why Positive Replacement Forms (Part 3)

Negative-only bans ("don't say X") leave the AI to invent replacements, often producing synonym-shaped failures: "evidently" substituted for the banned "obviously" shares the same epistemic failure mode at one level of indirection. Stating the positive replacement form as part of the rule constrains the substitution and gives the AI a target shape rather than only an exclusion zone.

### Why Compliance Theater (Part 3)

Phrase-level honest-framing tables catch surface violations but miss structural ones — outputs that pass every phrase check while violating the rule's intent. A defects-list with one entry per domain regardless of evidence satisfies a quota syntactically; a tools-used list with non-specific entries satisfies a coverage check syntactically; markers attached to non-claims raise marker density syntactically. The compliance-theater table names these structural failure modes so they can be diagnosed at the same level as anthropomorphism, hallucination, and fabrication.

---

## Prior Art Convergence, Stage 7, and Companion Document Rationale

The v2.6.0 additions (companion to walkthrough feedback session, 2026-05-05) address four structural gaps identified by RCA on the complete guide output.

### Why Stage 2b / Prior Art & Convergence Check ([RULE-030])

An iterative pipeline-test found the guide reinvented multiple well-documented constructs independently: IFEval's 25 verifiable constraint types (arXiv:2311.07911), FASTRIC's FSM formalization of transformer rules (arXiv:2512.18940), Anthropic's "context rot" framing for the H40 problem. The guide had no stage requiring external literature search before rule promotion. Stage 2b closes this by requiring a convergence map, simplification candidates, and gap analysis before Stage 3 for any governance artifact pipeline. The 70% convergence criterion is the quantitative trigger for "redesign from taxonomy" vs. "extend incident-driven set."

External prior art confirmed two things: (1) the guide's core structural choices are validated by independent research (IFEval's verifiable-constraint taxonomy maps directly to Rules 1, 3, 4; FASTRIC's FSMs map to transformer-rule shape); (2) the guide has at least one genuine gap (instruction position within the document — Gemini 3's finding that early negative constraints are dropped — not addressed by any current rule).

### Why Stage 7 / Whole-Output Coherence Review ([RULE-028])

The pipeline's six stages address individual-output quality: framing, routing, analysis, synthesis, critique, refinement. None address the complete output as a unit. The walkthrough of the completed guide found internal contradictions (scope statement referenced "prompt authoring task" without definition; retrofit status read as deferred when it was complete), cross-reference accuracy gaps, and document-type fit failures (background doc organized as design log rather than reference document). These are not detectable by any Stage 1–6 check because each stage audits its own output, not the complete artifact.

Stage 7 makes the whole-output coherence check structural — not aspirational — with four sub-checks and an explicit PASS/CORRECTED/BLOCKED verdict. The verdict is required before marking any full-pipeline output IMPLEMENTED.

### Why the Companion Document Structure Standard ([RULE-027])

`docs/design/` has `design-document-standards.md` governing the structure of documents in that directory. `docs/reference/` has no equivalent standard. The result: companion rationale documents grew by append (v2.1 → v2.2 → ... → v2.5 Patches: sections) until they became sequential design logs rather than topic-organized references. A first-time reader cannot navigate by problem.

RULE-027 closes the gap: companion rationale documents in `docs/reference/` must be organized by topic. The trigger is observable (≥3 section headings matching `vN.N Patches:` pattern). The fix for this document — renaming version-patch headings to topic names — is the reference implementation of RULE-027's required correction.

### Why the Scope Classification Decision Procedure ([RULE-029])

The three scope values (Authoring, Output, Process) were assigned by inspection during Package B of the coherence rework. No documented decision procedure existed. Without one, future rules could be misclassified: RULE-013 (epistemic markers) could appear Authoring-scoped (fires when authoring an investigation report) rather than Output-scoped (governs tokens emitted in responses); RULE-P01 (cross-stage handoff) could appear Authoring-scoped (fires when authoring a stage spec) rather than Process-scoped (governs stage boundaries). The three-question procedure (Q1: authoring-time trigger? → Authoring; Q2: response tokens? → Output; Q3: stage boundary? → Process) produces a deterministic assignment the author can self-apply and the reviewer can verify.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Two files (this + rule-design-standards.md) | The guide must follow [RULE-001] / Rule 1 itself. A verbose Claude-facing document full of motivation prose is a self-monitoring rule — Claude reads the "why," approximates the behavior, and executes the format obligation inconsistently. Motivation in a separate human-facing file keeps the Claude-facing guide as format obligations only. |
| Rules 1–8 numbering preserved | Existing cross-references in CLAUDE.md, tests, and skill files cite rule numbers; renumbering breaks them. Stable RULE-NNN IDs introduced in Package A of rule-design-standards-coherence-rework.md decouple identity from section numbering going forward. |
| Pipeline (Part 1) before rules (Part 2) | Macro structure (pipeline shape) before micro quality (instruction quality within stages). You design the pipeline before writing the rules into it. |
| "Required output shape:" explicit on each stage | Applies [RULE-001] / Rule 1 to the pipeline itself — the guide practices what it prescribes. Each pipeline stage is a format rule: the output must have a specific shape, not just follow general guidance. |
| Lightweight variant included | Not every problem warrants 6 full stages. Forcing the pipeline on simple tasks over-engineers the solution. The lightweight variant keeps the mindset shift (explicit framing → routing → critique) without the full template overhead. |
| Honest-framing vocabulary in the Claude-facing guide, not here | The vocabulary tables are actionable format rules — they tell Claude which phrases to flag and what to replace them with. They are not background reading; they are operational instructions. They stay in rule-design-standards.md. |

---

## Provenance

Two source documents were merged to produce the v2.0.0 Prompt Authoring Guide:

1. **Auto-Expert Prompt Building Guide** (external, provided 2026-04-29) — the pipeline design, failure-mode framing, and orchestration mindset. Originating session on an unrelated project; adapted for this use.

2. **Rule Design Standards v1.1.0** (in-repo, 2026-04-27) — the instruction quality rules, H40 framing, and honest-framing vocabulary. Independently validated by the source project's anti-patterns diagnosing the same failure modes.

**v2.1.0 source (2026-05-04):** Iterative pipeline-test producing a v1.0 → v1.5 delta on a complex pipeline prompt authored using v2.0.0 of the guide. The twelve patches between v1.0 and v1.5 of the test prompt mapped 1:1 to gaps in the guide that produced it. Patches were diagnosed at the meta-level (gaps in the guide, not the prompt) and integrated as v2.1 patches: [RULE-002] / Rule 1.1, [RULE-007] / Rule 5.1, [RULE-008] / Rule 5.2, [RULE-010] / Rule 6.1, [RULE-012] / Rule 7.1, new [RULE-020] / Rule 9 through [RULE-022] / Rule 11, Part 2 preamble meta-clause, Part 1 handoff + sequestration subsections, Part 3 positive-replacement column, Part 3 Compliance theater table, Quick-Reference Checklist additions. See the plan `rule-design-standards-pipeline-feedback.md` for design decisions and implementation sequence.

**v2.2.0 through v2.5.0 sources (2026-05-04):** Walkthrough rounds 2–3 (v2.2.0, v2.3.0, v2.3.1) and Coherence Rework program (v2.4.0, v2.5.0). See `rule-design-standards-coherence-rework.md` for the full coherence rework plan and implementation sequence.

**v2.6.0 source (2026-05-05):** Walkthrough feedback session on a deployment branch of the source project. Eight ERROR-level findings, 13 RCA feedback rows, 6 genuine L3 actions. Primary changes: scope statement enumeration, Stage 2b (Prior Art & Convergence Check), Stage 7 (Whole-Output Coherence Review), Rules 16–19 (RULE-027 through RULE-030), CLAUDE.md self-compliance gate, T5.35 retrofit (78 fields across 26 rule sections).

External prior art:

- **White et al. 2023, "A Prompt Pattern Catalog" (Vanderbilt)** — establishes prompt patterns as a knowledge-transfer form.
  - *Incorporated:* The framing of this guide as a localized, opinionated pattern set.
  - *Omitted:* Specific catalog patterns not relevant to the instruction-authoring domain.

- **Anthropic prompting best practices:** structured output, explicit formatting, context engineering.
  - *Incorporated:* Format-rule-over-self-monitoring preference (consistent with structured output guidance); explicit "Required output shape:" per stage (explicit formatting); stage-chaining as context engineering.
  - *Omitted:* (1) Worked examples per rule — Anthropic recommends at least one per instruction; current guide has examples for Rules 1 and 3 but not Rules 2, 4, 5, 6, 7. (2) Sub-agent orchestration policy — covered in CLAUDE.md but not cross-referenced from this guide's pipeline section. (3) Model-specific capability calibration — covered in `docs/reference/model-guidance.md`; cross-referenced from Part 1 Control Levers as of v2.0.0. (4) XML tag notation for structured input — not incorporated; guide uses markdown templates.
  - *Rationale for omissions:* (1) Worked examples deferred pending rule-by-rule review pass. (2–3) Cross-references to CLAUDE.md and model-guidance.md added to Part 1 (v2.0.0). (4) Markdown templates chosen for readability in this context; XML tags are not required.

- **Anthropic "Effective Context Engineering" (2025):** introduces "context rot" — as context grows, recall accuracy decreases. Named external equivalent for the H40 problem. The guide's transformer-rule form (Rule 1) is a direct response to context rot, independently arrived at. External validation found in Stage 2b run (2026-05-05).
  - *Incorporated:* "Context rot" named in Executive Summary and Core Problem as external validation for H40. `[Verified: Anthropic Engineering blog, 2025]`
  - *Gap:* Anthropic context engineering guidance includes model-context-length constraints affecting rule position within prompts; not yet addressed.

- **IFEval benchmark (White et al., 2023; arXiv:2311.07911):** defines 25 verifiable instruction constraint types; establishes Constraint Success Rate (CSR) metric. Independently converges with Rules 1, 3, 4 (verifiable by reading the artifact alone). Found during Stage 2b prior art search (2026-05-05).
  - *Incorporated:* IFEval's constraint taxonomy validates the guide's verifiability requirement for rules. Cited in Stage 2b as a convergence reference. `[Verified: arXiv:2311.07911]`
  - *Gap identified:* IFEval classifies constraints into format/content/style/structural categories — a cleaner taxonomy than the guide's current rule groupings. Rule consolidation against IFEval taxonomy is a candidate simplification (backlog: T5.37 prior art currency gate).

- **FASTRIC: Prompt Specification Language (2025; arXiv:2512.18940v1):** models prompt interactions as explicit finite state machines. Transformer-form rules (subject + trigger + permitted values) are informal FSM transitions. Independently converges with Rule 1 (transformer form) and the trigger features / borderline cases structure. Found during Stage 2b prior art search (2026-05-05).
  - *Incorporated:* FASTRIC's FSM model named as external validation for transformer-rule shape in § Prior Art Convergence rationale. `[Verified: arXiv:2512.18940v1]`
  - *Omitted:* FASTRIC's conformance verification through execution trace analysis — not incorporated; this guide relies on self-check lines rather than formal trace verification.

- **Google Gemini 3 Prompting Guide (2025):** finds that instruction position within the prompt matters — negative constraints appearing early are more likely to be dropped. No current rule in this guide addresses instruction position.
  - *Gap identified (not yet incorporated):* Add a rule or checklist item for instruction position: constraints stated late in an instruction document are more salient than constraints stated early. Backlog item candidate.

- **Reducto Pipeline IDs, n8n Workflow IDs, AWS Data Pipeline, Pulumi Harness, GitLab CI:** stable pipeline identifiers as the primary handle for pipeline references. ([Reducto](https://llms.reducto.ai/pipeline-ids), [n8n](https://docs.n8n.io/workflows/workflow-id/), [Pulumi Harness Pipeline](https://www.pulumi.com/registry/packages/harness/api-docs/platform/pipeline/))
  - *Incorporated:* `[PIPELINE-NNN]` ID form (v2.8.0); Pipeline Registry table pattern in Part 1; the principle that the ID outlives version changes.
  - *Omitted:* Runtime resolution — external systems mechanically resolve pipeline IDs to executable configurations. Our use is documentation-tier where the ID is read by humans and AIs, not mechanically resolved.

- **Anthropic Agent Skills (Dec 2025):** progressive disclosure pattern — skill name and description pre-loaded into agent's system prompt at startup, allowing dynamic detection of which skills are available. ([Anthropic Engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills))
  - *Incorporated as divergence rationale:* Anthropic's progressive disclosure is runtime; our requirement is authoring-time. We adopt the deployment-target taxonomy concept but locate it in the authoring workflow.

- **SpecWeave Agent Skills extensibility analysis (2025):** "not all agents can run bash commands, create files, or access the network, requiring instructions that degrade gracefully." ([SpecWeave](https://spec-weave.com/docs/guides/agent-skills-extensibility-analysis/))
  - *Incorporated:* Capability-tier framing for the per-target applicability declaration in RULE-031 (v2.8.0).
  - *Omitted:* Agent-side runtime detection — our use is authoring-time.

- **Unleash FeatureOps "Graceful degradation in practice" (2025):** feature availability matrix and capability-tier vocabulary. ([Unleash](https://www.getunleash.io/blog/graceful-degradation-featureops-resilience))
  - *Incorporated:* Per-target capability-tier vocabulary (Available / Documentation-only fallback / Not enforceable on this deployment target).

- **Promptware Engineering: Software Engineering for Prompt-Enabled Systems (2025; arXiv:2503.02400v2):** frames prompts as software with portability concerns. ([arXiv](https://arxiv.org/html/2503.02400v2))
  - *Incorporated as background citation:* validates the framing that prompts deserve software-engineering-grade portability practices, but doesn't supply a specific deployment-target taxonomy.

---

## Changelog

v1.7.1 — 2026-05-08: Terminology migration — Surface → Deployment Target (companion to `rule-design-standards.md` v2.8.1).
- Renamed § Multi-Surface Guidance Rationale → § Multi-Deployment-Target Guidance Rationale; anchor link in Executive Summary updated.
- Added subsection "Why 'Deployment Target' was chosen over 'Surface' (v2.8.1 rename)" — documents the retroactive rename test and the choice rationale (CI/CD vocabulary alignment, future MCP / custom-connector accommodation).
- Body text rename: surface → deployment target throughout the new section. Pre-existing usages of "surface" in this document (Rule-1 surface-feature, surface-of-the-output, "the model will surface tradeoffs") refer to different concepts and remain unchanged.
- Provenance entries updated to use "deployment-target" vocabulary where they referenced the v2.8.0 work.

v1.7.0 — 2026-05-08: Multi-deployment-target guidance + pipeline naming convention rationale (companion to `rule-design-standards.md` v2.8.0).
- Added § Multi-Deployment-Target Guidance Rationale (originally Multi-Surface Guidance Rationale; renamed in v1.7.1): three-target taxonomy (Claude Code Local, Claude Code Remote, Claude Chat); why infrastructure-dependent rules need per-target declarations; collapse pattern of RULE-011, RULE-023, RULE-025, Stage 7c, `[PA]` row on Claude Chat; asymmetric note about Claude Chat's narrower context as offsetting advantage; misclassification authoring test for RULE-025; output-scope rule exemption.
- Added § Pipeline Naming Convention Rationale: stable `[PIPELINE-NNN]` IDs; Pipeline Registry table pattern; rationale for renaming "Lightweight Variant" to "Lightweight Pipeline" with closed synonym list; adding-a-new-pipeline workflow.
- Updated Executive Summary navigation list to include the two new sections.
- Updated Provenance with prior art citations: Reducto Pipeline IDs, n8n Workflow IDs, Pulumi Harness, Anthropic Agent Skills, SpecWeave capability tiers, Unleash FeatureOps, Promptware Engineering.

v1.6.0 — 2026-05-05: Topic-organized restructure (RULE-027 compliance) + v2.6 rationale additions.
- Renamed all version-patch section headings (`v2.5 Patches:`, `v2.4 Patches:`, `v2.3 Patches:`, `v2.2 Patches:`, `v2.1 Patches:`) to topic-oriented names. Section content unchanged.
- Fixed "Why Rules 1–8 were deferred" heading → "Why Rules 1–8 were initially deferred (resolved v2.3.1)"; added resolution note documenting the v2.3.1 completion. (feedback row 1)
- Updated Executive Summary to list all topic sections by name. (feedback row 2)
- Added § Prior Art Convergence, Stage 7, and Companion Document Rationale: rationale for Stage 2b (RULE-030), Stage 7 / RULE-028, RULE-027 (companion doc structure), RULE-029 (scope classification). (feedback rows 9, 10, 11, 12)
- Added v1.3.1 changelog entry (below). Companion to `rule-design-standards.md` v2.6.0.

v1.3.1 — 2026-05-04: Added resolution note to the "Why Rules 1–8 were initially deferred" section documenting that Package B (coherence-rework plan, 2026-05-04) completed the retrofit. No substantive content changed; resolution note retroactively applied to the v1.3.0 section.

v1.5.0 — 2026-05-04: Added "Pipeline Integrity Gates Rationale" section with rationale for [RULE-025] / Rule 14 (Pipeline-bypass detection) and [RULE-026] / Rule 15 (First-time-reader gate). Added executive summary. Updated all section-heading rule references to include stable RULE-NNN IDs alongside rule numbers. Updated Provenance with v2.2.0–v2.5.0 source note. Companion to `rule-design-standards.md` v2.5.0.

v1.4.0 — 2026-05-04: Added "v2.4 Patches: Coherence Rework — Enforcement & Disambiguation Rationale" section with rationale for [RULE-023] / Rule 12 (Enforcement location) and [RULE-024] / Rule 13 (Trigger vocabulary disambiguation). Companion to `rule-design-standards.md` v2.4.0.

v1.3.0 — 2026-05-04: Added "v2.3 Patches: Walkthrough Round 3 Rationale" section with four subsections: bare-noun-phrase subjects, qualifiers-in-permitted-values, Rules-1–8 deferral, per-rule-field-requirement structural choice. Companion to `rule-design-standards.md` v2.3.0.

v1.2.0 — 2026-05-04: Added "v2.2 Patches: Walkthrough Round 2 Rationale" section with five subsections covering the transformer/conditional axis, structural Self-check pattern, Part 3 catch-all rewrites, linter vocabulary high-precision split, and Quick-Reference Checklist grouping. Companion to `rule-design-standards.md` v2.2.0.

v1.1.0 — 2026-05-04: Added "v2.1 Patches: Pipeline-Test Feedback Rationale" section with one rationale subsection per new rule / extended sub-clause / Part 1 subsection / Part 3 addition. Updated Provenance with the iterative pipeline-test source. Companion to `rule-design-standards.md` v2.1.0. See the plan `rule-design-standards-pipeline-feedback.md`.

v1.0.0 — 2026-04-29: Created as companion to `rule-design-standards.md` v2.0.0. Incorporates the 8 failure-mode drivers from the Auto-Expert Prompt Building Guide, the H40 and three-tier enforcement rationale from Rule Design Standards v1.1.0, and design decisions for the two-file structure.
