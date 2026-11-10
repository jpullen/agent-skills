# Attribution

This file credits the work the kit grew from and the sources its authoring guide cites. Each entry names an influence or a source. None of the people or organisations named here wrote, reviewed or endorsed this repository.

## Origin

The graph prompt this kit grew from is by @hanakoxbt. It was inspired by Andrej Karpathy's autoresearch, with a graph adaptation from @hanakoxbt's agent-layers guide. The footer of the original prompt card reads:

> Prompt by @hanakoxbt. Inspired by Karpathy's autoresearch [1]; graph adaptation from my agent-layers guide [2]. [1] github.com/karpathy/autoresearch [2] agent-layers.vercel.app. Original wording and workflow adaptation by @hanakoxbt. Not written or endorsed by Andrej Karpathy.

References as printed there:

1. github.com/karpathy/autoresearch
2. agent-layers.vercel.app

Original post: (link to be added by the author)

The kit kept from that prompt its tag structure, from goal through delivery, and its bounded-node idea. The later design is the author's: gates checked with planted mutants, the schema-validated run record, and the calibration runs.

## Andrej Karpathy — autoresearch

The original prompt states these five principles, which it adapts from Karpathy's autoresearch (https://github.com/karpathy/autoresearch, March 2026):

1. Establish a baseline before changing the system.
2. Give every node one clear scope and a fixed evaluator.
3. Change one thing, measure it, and keep useful improvements.
4. Record failed attempts too.
5. Prefer fewer nodes when results are comparable.

## Related ideas

A later review identified these other public ideas by Andrej Karpathy as related to parts of the kit. They are not sources the kit was built from.

- "Software Is Changing (Again)", YC AI Startup School keynote, published 2025-06-18: https://www.youtube.com/watch?v=LCEmiRjPEtQ. Its chapters on partial autonomy and autonomy sliders relate to the kit's gates, where the person approves.
- karpathy/llm-council, 2025-11-22: https://github.com/karpathy/llm-council. It anonymizes model identities so a model cannot play favorites when judging outputs, which resembles the kit's reviewer that judges work without knowing its author.
- "Verifiability", 2025-11-17: https://karpathy.bearblog.dev/verifiability/. Its claim that Software 2.0 easily automates what you can verify relates to the kit's emphasis on checks that can fail.
- "context engineering", a term he promoted over "prompt engineering", 2025-06-25: https://x.com/karpathy/status/1937902205765607626. The term only, not a method.

## Prior art cited by the Prompt Authoring Guide

The Provenance section of `plugins/prompt-authoring/skills/prompt-authoring/references/prompt-authoring-background.md` cites these external references; links are as printed there where it gives one.

- White et al. 2023, "A Prompt Pattern Catalog" (Vanderbilt).
- Anthropic prompting best practices: structured output, explicit formatting, context engineering.
- Anthropic "Effective Context Engineering" (2025), which introduces "context rot".
- IFEval benchmark (White et al., 2023; arXiv:2311.07911).
- FASTRIC: Prompt Specification Language (2025; arXiv:2512.18940v1).
- Google Gemini 3 Prompting Guide (2025).
- Pipeline identifiers: Reducto ([Reducto](https://llms.reducto.ai/pipeline-ids)), n8n ([n8n](https://docs.n8n.io/workflows/workflow-id/)), AWS Data Pipeline, Pulumi Harness ([Pulumi Harness Pipeline](https://www.pulumi.com/registry/packages/harness/api-docs/platform/pipeline/)), GitLab CI.
- Anthropic Agent Skills (Dec 2025): [Anthropic Engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).
- SpecWeave Agent Skills extensibility analysis (2025): [SpecWeave](https://spec-weave.com/docs/guides/agent-skills-extensibility-analysis/).
- Unleash FeatureOps, "Graceful degradation in practice" (2025): [Unleash](https://www.getunleash.io/blog/graceful-degradation-featureops-resilience).
- Promptware Engineering: Software Engineering for Prompt-Enabled Systems (2025; arXiv:2503.02400v2): [arXiv](https://arxiv.org/html/2503.02400v2).

The guide also draws on two source documents named in the same section: an external Auto-Expert Prompt Building Guide and the author's own Rule Design Standards v1.1.0.

None of the people or organisations named in this file wrote, reviewed or endorsed this repository.
