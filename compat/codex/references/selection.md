# Select the execution method

Every execution plan must contain an **Execution route**. Permitted values: `graph` with the dependent outputs, acceptance gates, selected source and available review capability; `direct` with the bounded outcome and its check; or `unresolved` with the missing capability and the independent work that can proceed. Use the existing task record rather than another registry.

The default assessment is inexpensive: identify the actual deliverable dependencies and acceptance obligations before loading the full prompt. Select graph execution when intermediate outputs need separate acceptance before downstream work, when reconciling multiple sources needs distinct content and integration checks, or when work crosses repository or reviewer handoffs. An analysis of alternatives with source qualification, option analysis and independent acceptance is a graph candidate. Prefer deterministic enumeration, transformation and checking inside either route.

Select direct execution for a factual lookup, unchanged-status reconciliation, an isolated edit with a known affected check, or a deterministic batch with one acceptance outcome. A batch touching many files is not automatically a graph. A one-node graph is available when an explicit graph record is itself requested, but it is not mandatory for simple work. A user request for a different method controls; retain any applicable repository validation and authorization obligations.

Before starting graph builders, use the preflight contract. If fresh-context review, adequate measured capacity or required source evidence is absent, record the unavailable gate. Continue independent preparation or use a disclosed direct route where it satisfies the real outcome; do not relabel a required independent gate as passed. A planned gate is not an executed check. Do not introduce a hard graph-run cap as if the user requested it.

Method selection is a task decision, not an assertion of measured cost or universal quality. A graph record supports inspectable dependencies and gate results; it does not establish that the method is faster, cheaper or correct for every task. Keep unavailable model/cost telemetry explicit.

Where root instructions select this skill, use that selection. A consumer that binds the utility through an exact reviewed tool binding keeps that binding separate from the product's governance/model binding. An unmerged source may be evaluated under explicit user authorization but remains a candidate. After source integration, reconcile the final immutable revision and manifests before consumer activation. Do not copy a second editable policy master or fetch floating main. Update the upstream archive, adaptation and regression evidence separately on each new Claude release.

Trigger features: task planning, dependent outputs, acceptance gate, source reconciliation, repository handoff.
Borderline cases: A typo plus one affected check selects direct; an analysis combining requirements, alternatives and separate content/integration acceptance selects graph. A multi-file mechanical replacement with one acceptance check selects direct unless the user requests a graph record.
Quota exit: None — no count threshold in this rule; observable dependencies and required acceptance determine the route.
Brevity allowance: Execution route may use minimal — one exact outcome and reason; missing gates remain explicit.
Falsifiability: threshold: 0 claimed graph completions with missing required gates; horizon: one selected task; role: independent outcome reviewer comparing the request, route and actual evidence.
Applicability: Applies in all contexts selecting this utility, subject to user direction, actual project bindings and higher-priority rules.
Procedural form: Trigger: task planning or release qualification; Steps: identify outputs and gates, record the route and reasons, execute the selected procedure, retain actual checks and unresolved scope; Output: Execution route and the route's evidence.
Pipeline applicability: Per-stage applicability: selection supplies route and outcome to preparation; graph preparation supplies frozen sources and gates to execution; direct work supplies its outcome and check to delivery; delivery consumes observed results, not promised gates.
Fields consumed by next stage: Execution route, outcome, checks, selected source and unavailable capability.
Sequestered: None — this stage IS the evaluation stage (candidate execution methods introduced here as input).
Self-check: Every execution plan is a bare subject; Execution route permits graph, direct and unresolved outcomes without a universal graph mandate.
