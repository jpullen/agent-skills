---
name: prompt-authoring
description: Author or revise durable AI instructions (CLAUDE.md, SKILL.md, prompt files, rule sets) to the Prompt Authoring Guide's format rules, or audit existing instructions against them.
when_to_use: Use when the person asks to write, edit, tighten, review or audit a CLAUDE.md, a SKILL.md, a system prompt or prompt file, a rule set, a plan template or an experiment contract. Trigger phrases - "write a CLAUDE.md", "add a rule to my CLAUDE.md", "write a skill", "revise these instructions", "review this prompt", "audit my rules", "is this rule enforceable", "why does the model ignore this instruction", "make this rule testable", "write a design document". Also use before changing the guide itself.
---

# Prompt Authoring

This skill applies the Prompt Authoring Guide (v2.9.0) to durable instructions for AI. It holds no rules itself. The rules live in the reference files below; read the part that matches the task, and follow it.

## Reference files

| File | What it is | When to read it |
|---|---|---|
| [rule-design-standards.md](references/rule-design-standards.md) | The Prompt Authoring Guide: the instructions to follow | Every authoring, revising or auditing task |
| [prompt-authoring-background.md](references/prompt-authoring-background.md) | The reasoning behind each rule | Only when asked why a rule exists, when two rules seem to conflict, or when proposing a change to the guide. Do not load it for routine authoring: it states why rationale is kept apart from the rules |
| [design-document-standards.md](references/design-document-standards.md) | A separate standard for documents that define entities, relationships or architectural patterns | When the artifact is a design document |

## Procedure

1. Name the artifact kind being written or changed.
2. Read the guide's header block (Scope, Out of scope, Enforcement) in `references/rule-design-standards.md`. It decides whether the guide applies to this artifact and which edits make it required reading. If the artifact is out of scope, say so and stop applying the guide.
3. Read the guide's Part 2 preamble, then the rule sections that match the task. Part 2 holds the format rules for instructions; each rule section carries its own trigger features and borderline cases, so match the artifact against those rather than against a summary.
4. If the artifact contains a multi-stage prompt or pipeline, read Part 1 (its Pipeline Registry says which pipeline definition applies). The full-pipeline specification is the `pipeline-001` skill in this plugin, which the person invokes directly.
5. If the artifact makes or reports claims about causes, evidence or external facts, read Part 3 (the honest-framing vocabulary).
6. If the artifact's rules cite infrastructure that may be absent where it will run (hooks, tests, a file system, a backlog), read the rule section on deployment-target applicability before finishing.
7. Before returning the artifact, walk the Quick-Reference Checklist at the end of the guide and correct each row that fails.
8. Report which rule sections were applied and which checklist rows needed a fix. Do not claim a rule was applied unless the artifact now satisfies it.

## Obligations (pointers only)

- Which artifacts the guide covers, and when reading it is required: the header block of `references/rule-design-standards.md`.
- How a rule must be shaped, scoped, tested and enforced: Part 2 of the guide.
- How output wording must treat evidence and certainty: Part 3 of the guide.
- How the guide applies to itself: the Part 2 preamble.
- What changed between guide versions: `CHANGELOG.md` at the plugin root, derived from the guide's own changelog.
- What was altered when the guide was rehomed into this plugin: `REHOMING-LEDGER.md` at the plugin root.

## Boundaries

- Rule identifiers in the guide (the bracketed `RULE-` ids) are stable; cite them in preference to section numbers.
- The guide governs the format of instructions. It does not decide what the instructions should say; that remains the person's call.
