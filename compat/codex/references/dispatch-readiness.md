# Source contract

Every dispatch readiness evaluation must contain a **Readiness disposition**. Permitted values: selected kit/runtime/source identities, quoted rule coverage, frozen checks and actual baseline receipts, packet, independent semantic review and seal verification; or None — preparation incomplete, with the failed or unrun prerequisite.

The following tested-candidate body retains its original meaning. This source-form contract supplies no runtime enforcement, independent approval or consumer adoption.

# Dispatch readiness contract

This companion gate implements the preparation requirement that the first external trial missed. It does not change the six-file graph record, infer all requirements from prose, establish genuine agent identity, or replace semantic review and final audits. The existing validator still checks the graph record. A valid record alone is insufficient to dispatch a builder.

Use this procedure for a **new run** before builder dispatch. Resuming an already sealed run uses `verify`; an old run without a seal cannot acquire a retroactive pre-dispatch receipt. Preserve unsuccessful packets and reviews. Source or contract changes require a new reviewed contract/run under the adapter; do not edit a sealed receipt to keep a green status.

## File layout and preparation

`RUN_DIR` must be outside the selected package; otherwise newly written runtime receipts would change the package fingerprint and invalidate their own packet. All selected source snapshots, baseline inputs/logs and frozen gates/briefs must be files within `RUN_DIR`; absolute paths, `..` and symlinks escaping that directory are rejected. Copy selected inputs into `RUN_DIR/sources/` and preserve their original location/revision in the source material or a frozen provenance file. Do not mutate baseline snapshots when the builder replaces its live output stub.

Create the six YAML files and `dispatch-plan.json` before invoking the tool. The six YAML files remain the canonical graph/check/progress representation. Every node must be `not_started`, no builder may already be registered, and all check rows must have attempt 1. Exec rows record the actual failing baseline; ordinary artifact-review rows remain unresolved with `isolation.kind: not_run`. A partial-exec baseline may already have a failed fresh residue adjudication as described below; that is not acceptance of the future builder's artifact.

The JSON companion has these exact required fields (extra explanatory fields are permitted):

```json
{
  "version": 1,
  "run_id": "example-rerun",
  "author": "/root/trial-controller",
  "sources": [
    {
      "id": "user-task",
      "path": "sources/user-task.txt",
      "sha256": "<64 lowercase hexadecimal characters>",
      "role": "normative",
      "scope": "Full user task and explicit clarification; no architecture adoption"
    }
  ],
  "coverage": [
    {
      "rule_id": "compare-options",
      "source_id": "user-task",
      "checks": ["node:option:semantics", "acceptance:content"],
      "unchecked_reason": null
    }
  ],
  "acceptance": [
    {
      "id": "content",
      "type": "review",
      "requirement": "<exact initial row requirement>",
      "fails_when": "<exact initial row fails_when>",
      "exercises": ["compare-options"],
      "red_plan": "<one deliberately removed or contradicted property named in fails_when>"
    },
    {
      "id": "structure",
      "type": "exec",
      "requirement": "<exact initial row requirement>",
      "fails_when": "<exact initial row fails_when>",
      "exercises": [],
      "red_plan": "<actual baseline assertion and intended discrimination>"
    }
  ],
  "integration": {
    "requirement": "<exact initial integration row requirement>",
    "fails_when": "<exact initial integration row fails_when>",
    "red_plan": "<actual baseline assertion and intended discrimination>"
  },
  "baselines": [
    {"check": "node:option:structure", "receipt": "evidence/node-baseline.json"},
    {"check": "acceptance:structure", "receipt": "evidence/final-baseline.json"},
    {"check": "integration", "receipt": "evidence/integration-baseline.json"}
  ],
  "frozen_files": ["code/structure.py", "code/integration.py", "briefs/review.txt", "scope-and-provenance.txt"]
}
```

The example is explanatory, not an executable passing fixture. Use the actual run's IDs, exact definitions, quotes, hashes and observed receipts.

### Source and requirement mapping

Source roles are `normative` or `evidence`; every source needs a nonempty scope and matching digest. A document's presence does not make its instructions authoritative. Select the real user request, applicable instruction scope and accepted requirements explicitly; preserve reference/prototype/superseded sources as evidence. Scope declarations must not omit inconvenient requirements. The independent reviewer assesses that selection and the inventory against the supplied material.

Every `rules.yaml` rule has exactly one coverage entry. Its `spec` equals the selected normative source ID and its literal `quote` must occur in that source's saved body; `section` supplies the location/context. Every normative source must contribute at least one rule. This detects missing references and missing inventory entries, **not** an omitted sentence that was never entered as a rule.

Coverage targets use `node:NODE:CHECK`, `acceptance:ITEM`, or `integration`. An exercised rule has one or more targets and `unchecked_reason: null`. An unchecked rule has `checks: []` and a substantive reason. Acceptance `exercises` and coverage mappings must agree in both directions. Report unchecked rules explicitly; they are never silently counted as checked.

All node checks and each final acceptance item require initial rows. Node row type, requirement and fails_when must exactly match the graph definition. Acceptance rows match the companion definition including exercises; the integration row matches its companion definition. Later verdict/evidence changes are allowed, but changing a frozen check definition invalidates readiness.

### Actual baseline receipts

Every exec node check, exec acceptance item and integration check needs a captured assertion-red receipt before dispatch. A future `red_plan`, an import failure, or a missing-path error is insufficient. Each receipt has:

```json
{
  "command": ["/actual/selected/python", "code/structure.py"],
  "cwd": "/actual/run/directory",
  "actual_exit": 1,
  "assertion_failures": 1,
  "log_path": "evidence/baseline.log",
  "inputs": [
    {"path": "evidence/baseline-input.json", "sha256": "<actual captured-input digest>"}
  ]
}
```

The tool checks nonzero exit, positive assertion count, an existing log containing `AssertionError` or `assertion failure`, input digests and agreement with the initial failing exec row. It freezes the receipt, log and input files. It does not authenticate a claimed command or infer whether an assertion actually exercises the intended requirement; the semantic readiness review and evidence audit must assess that. Reuse one baseline receipt only where it is the same actual defined execution, and disclose shared execution rather than claiming multiple runs.

### Partial-exec residue reviews

When a graph check uses `exec_available: partial`, its implicit `<check>-residue` review row must also be planned and frozen. Add exactly one `residue_reviews` entry for each such parent check:

```json
{
  "check": "node:option:filter",
  "requirement": "Adjudicate every flagged baseline item",
  "fails_when": "<exact parent check fails_when>",
  "red_plan": "<one planted violation in the flagged-list mutant>",
  "baseline_review": "evidence/filter-residue-baseline.json"
}
```

The graph's `residue` brief remains part of the frozen graph. The companion adds the exact implicit-row requirement and evidence binding; it does not weaken the parent criterion. Coverage may target `node:option:filter-residue`, and the independent readiness review must include every implicit target in `residue_coverage` (omit that array only when there are no partial checks).

The saved baseline-review receipt contains `reviewer` (actual native ID), `verdict: fail`, and `artifact_path/artifact_sha256`, `mutant_path/mutant_sha256`, `output_path/output_sha256`. All paths are contained, nonempty saved files. The mutant must differ from the flagged artifact. The reviewer must be registered on the parent node, differ from the plan author, and match the failed fresh-subagent residue row. That row cites the saved mutant in `red_evidence.variant_path` and review output in `evidence.path`. Its mutant red evidence and matching parent exec verdict remain subject to X28.

This permits the actual failing residue adjudication needed to establish a partial filter's negative baseline; it does not permit an ordinary review gate to claim a future artifact passed. A missing/degraded/not-run residue review remains an incomplete record, not conformant dispatch readiness. Its claimed identity, execution, complete adjudication and meaningful mutant still require independent review/audit, not just matching JSON fields.

## Prepare, independently review, seal, verify

Use the selected dependency-equipped interpreter consistently:

```text
python scripts/preflight.py prepare RUN_DIR --models inherited
python scripts/preflight.py seal RUN_DIR --models inherited
python scripts/preflight.py verify RUN_DIR --models inherited
```

`prepare` checks the Python environment (`PyYAML`, `jsonschema`), invokes the existing validator with the same interpreter, checks the companion and writes an **exclusive** `review-packet.json`. It prints that packet's SHA-256. Missing dependencies or failed prerequisites produce `not_ready`, exit 2, without a packet. `seal` also exits 2 unless the current contract still matches the packet and an independent coverage review passes.

Between prepare and seal, give a fresh reviewer the exact packet, sources, scope/instruction provenance, derived rules, check definitions, baseline receipts and logs. The reviewer assesses inventory completeness, source selection/reading limits, meaningful rule-to-check coverage, valid red controls and final acceptance. Do not fabricate a review or reuse a review for another digest. The reviewer writes `dispatch-review.json`:

```json
{
  "packet_sha256": "<SHA-256 of review-packet.json bytes>",
  "reviewer": "/actual/native/reviewer-id",
  "independent_of": ["/actual/plan-author-id"],
  "verdict": "pass",
  "source_coverage": ["<all selected source IDs>"],
  "rule_coverage": ["<all derived rule IDs>"],
  "acceptance_coverage": ["<all final acceptance IDs>"],
  "notes": ["<actual findings, scope/read limits and reasons for the verdict>"]
}
```

The coverage arrays must match the packet's sets completely, and notes must contain actual rationale and scope limits rather than an empty list. Native ID difference and the declared independence are checked structurally; actual fresh-context dispatch evidence remains the controller's responsibility. A fail/incomplete/stale review cannot seal. If correction is required, preserve the failed packet/review and prepare a new named packet via `--packet`; select its matching `--review`. Do not overwrite history.

`seal` creates exclusive `dispatch-seal.json` containing packet/review digests and a timestamp. `verify` checks those exact records, source/gate hashes, selected Python/dependency versions and the full selected package fingerprint (including skill, adapter, prompt, instructions and tools; excluding `.git`, `.pytest_cache`, `__pycache__` and `.DS_Store`). Package changes, additions or removals invalidate the packet; cache writes do not. Package directory symlinks are rejected, as are dangling or externally targeted file symlinks, so a linked subtree cannot silently evade fingerprinting. It permits mutable progress, verdict/evidence and lesson updates; graph/framing/rules/plan, baseline files and `frozen_files` remain unchanged. Do not put `checks.yaml`, `progress.yaml` or `lessons.yaml` in `frozen_files`; check definitions are protected separately. When carried evidence appears later, pass the current verified `--artifacts node=sha256,...` map through to the existing validator. The map is runtime data, not a pre-dispatch artifact identity.

All modes accept `--packet`, `--review` and `--seal` relative filenames. Verify follows the paths recorded in the selected seal. A new seal is not an authorization to reuse accepted results under changed requirements. The selected adapter determines invalidation and new-run behavior.

Run `verify` immediately before dispatch and when checking continuing readiness. Record the actual invocation in the controller's event ledger. The tool does not intercept all host actions, enforce the event budget, certify full governance semantic reading, or prove whole-run completion. Maintain real builder/reviewer/auditor dispatch receipts, count required invocations, and execute final acceptance and both audits separately.

## Regression coverage

`python -m pytest -q tests/test_preflight.py` covers successful preparation/sealing/continued verification; missing mappings/acceptance; unknown targets; unquoted requirements; absent and assertion-free baselines; path/symlink escape; source/gate/row/review drift; incomplete/stale/self reviews; explicit unchecked rules; duplicate JSON keys; dependency failure; and exclusive packet/seal creation. These use clearly labelled synthetic review fixtures. They do not constitute a real architecture review.


Trigger features: prepare, independent coverage review, seal, verify, builder dispatch.
Borderline cases: A schema-valid record without complete semantic coverage remains not_ready; an explicit unchecked rule remains visible and does not count as checked.
Quota exit: None — no count threshold in this rule; selected runtime limits bound work without imposing a findings quota.
Brevity allowance: unchanged or inapplicable context may use minimal — one exact reason; evidence identities and unrun work remain explicit.
Falsifiability: threshold: 0 passing dispositions with a missing required prerequisite or unsupported execution claim; horizon: one run and changed-source recovery; role: qualified reviewer comparing saved artifacts, raw observations and the disposition.
Applicability: Applies in all contexts selecting this optional utility, subject to higher-priority instructions and actual task authority.
Procedural form: Trigger: prepare, independent coverage review, seal, verify, builder dispatch; Steps: prepare exact inputs and baselines, create packet, obtain independent semantic review, seal and verify before dispatch, retain failed and changed-source outcomes; Output: Readiness disposition.
Pipeline applicability: Per-stage applicability: preparation passes source/rule/check/baseline identities to review; review passes packet digest, coverage and notes to sealing; verification consumes sealed identities before dispatch; builder inputs exclude reviewer reasoning and prior outputs.
Self-check: Every dispatch readiness evaluation is a bare subject; Readiness disposition includes observed evidence and an explicit None case. Field presence does not authenticate runtime behavior or semantic completeness.
