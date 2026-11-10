---
name: graph-record
description: Validate, report on, and check rule coverage of a graph-prompt run record (the directory of YAML files a graph-prompt run writes), using the graph-record kit's validate.py, coverage.py and report.py.
when_to_use: Use when the person says "validate the run record", "is the record complete", "check rule coverage", "which rules are unchecked", or "give me the delivery report", or points at a run directory holding graph.yaml, checks.yaml and progress.yaml (with framing.yaml, rules.yaml, lessons.yaml).
allowed-tools: Bash(python3 *)
disable-model-invocation: false
---

# graph-record

Three read-only scripts over a graph-prompt run record. RUN_DIR below is the run directory: `graph.yaml`, `checks.yaml`, `progress.yaml`, `framing.yaml`, `rules.yaml`, `lessons.yaml`. None of the three scripts writes into RUN_DIR.

Dependencies: `python3` and `pyyaml` for all three; `jsonschema` in addition for `validate.py`. coverage.py and report.py need only the standard library plus pyyaml; report.py imports coverage.py from the same `scripts/` directory.

Run them in this order: validate.py, coverage.py, report.py. report.py does not validate the record (it checks only the fields it reads, and exits 2 if one is missing or mistyped), so run validate.py first.

## validate.py

```
python3 ${CLAUDE_SKILL_DIR}/scripts/validate.py RUN_DIR --models haiku,sonnet,opus [--artifacts node=sha256,...] [--all]
```

- `--models` is the comma-separated model ladder the run used, cheapest first, as runtime model IDs, distinct and nonempty. Without it the tier rules X07 and X08 cannot be checked: `validate.py example` (no `--models`) exits 1 with `X08 run: --models ladder required to check tiers (X07, X08)`. Pass the run's own ladder; `haiku,sonnet,opus` is the ladder the bundled example validates under.
- `--artifacts node=sha256,...` supplies hashes for X11 (64 lowercase hex digits per entry, unique node names).
- `--all` prints every finding; the default prints the first and a `... N more (use --all)` line.

Order of work: JSON Schema validation, then the cross-file rules X01 to X33. Cross-file rules are skipped while schema findings exist (a `NOTE run: cross-file rules not evaluated while schema findings exist` line says so).

Exit codes:
- 0: the record conforms. Stdout is `OK <dir>: schema + crossfile hold`, plus `; N prose rule(s) in rules.yaml concern the record and need manual check` when X19 applies.
- 1: findings, printed as `<rule> <subject>: <message>`. A missing `graph.yaml`, `checks.yaml`, `progress.yaml`, `framing.yaml` or `rules.yaml` also lands here (a schema finding such as `SCHEMA <root>: 'graph' is a required property`), not at 2. A missing `lessons.yaml` is not an error: validate.py exits 0 without it.
- 2: usage or parse error (unreadable YAML, a duplicate mapping key, a malformed `--models` list (such as `a,,b`) or `--artifacts` value, a missing RUN_DIR argument). A `usage:` line goes to stderr. An empty `--models ""` is treated as no ladder, so it exits 1 with the X08 line, not 2.

Exit 0 does not establish: completion, that an artifact exists, that a tool actually ran, provenance, fresh context, complete review coverage, or an all-pass accepted state while rows remain unresolved. The X19 prose rules in `rules.yaml` are counted, not checked: they need a manual read. Agent IDs are accepted as recorded; that does not show the agent ran or was isolated. Source quotation is attribution, not evidence that the quoted claim is true. Source and permission claims and recorded model tiers need runtime evidence. The prompt's completion check and independent evidence audit are still required.

## coverage.py

```
python3 ${CLAUDE_SKILL_DIR}/scripts/coverage.py RUN_DIR [--markdown]
```

Reads `rules.yaml`, `checks.yaml` and `progress.yaml`. Contract: `scripts/COVERAGE-SPEC.md`.

For every rule whose `concerns` includes `deliverable`, one line `<rule id><TAB><bucket>[<TAB><detail>]`, then `summary: exercised=N unchecked=N uncovered=N`, then findings, then a `manual (not counted in the summary):` section for rules that do not concern the deliverable.

- `exercised`: an acceptance row names the rule in `exercises`. Detail is `item#attempt=verdict` per exercising item, from that item's newest attempt. The row's verdict does not decide the bucket.
- `unchecked`: no acceptance row exercises it and `progress.unchecked_rules` lists it. Detail is the reason.
- `uncovered`: neither. No detail field.

`--markdown` prints the same content as one table headed `| Rule | Bucket | Detail |`.

Exit codes:
- 0: X32 holds: no uncovered rule, and no `unchecked_rules` id that is not a rule id or is also exercised.
- 1: X32 does not hold; the findings are printed (`X32 ...` lines). `X09` findings (an `exercises` id that is not a rule id) are printed too but do not change the exit code.
- 2: usage or parse error (no RUN_DIR, an unknown option such as `--help`, RUN_DIR not a directory, a missing file, bad YAML, a duplicate key). A `usage:` line goes to stderr and stdout stays empty.

Exit 0 is a coverage check, not completion: it does not show that the exercising rows passed or that the rules hold. coverage.py does not validate the record against the schema. It reads `exercises` on acceptance rows only, and so does validate.py's X32, so the two agree on which rules are uncovered: a rule named only in the `exercises` of a non-acceptance row (for example the integration row) is uncovered in both (checked on a copy of `example/`: both exit 1).

## report.py

```
python3 ${CLAUDE_SKILL_DIR}/scripts/report.py RUN_DIR [--markdown]
```

Reads `rules.yaml`, `checks.yaml`, `progress.yaml` and `framing.yaml` (not `graph.yaml` or `lessons.yaml`). Contract: `scripts/REPORT-SPEC.md`.

Prints ten sections, each a `## <Heading>` line then `count: N`: Checked, Passed, Failed, Unresolved, Dissent, Escalated, Unchecked rules, Assumptions, Audits, Usage. It ends with `status: complete` or `status: partial`. Each subject (a node check, acceptance item, or the integration check) is counted once, at its latest attempt. With `--markdown` the items render as tables; headings, counts and the status line are the same. The Unchecked rules section is built from coverage.py's analysis.

Exit codes:
- 0: `status: complete`. All four hold as the record states them: every node is accepted (the `progress.graph` lists `running`, `failed`, `blocked`, `dissent`, `escalated`, `not_started` are empty); every subject's latest verdict is `pass`; `progress.audits.wellformed.exit_code` is 0 and `progress.audits.evidence.verdict` is `pass`; `progress.next_action.kind` is `delivery`.
- 1: `status: partial`. The whole report is still printed.
- 2: usage or parse error (no RUN_DIR, an unknown option such as `--help`, RUN_DIR not a directory, a missing or malformed file, or a missing or mistyped required field). A `usage:` line goes to stderr and stdout stays empty.

Exit 0 does not establish that anything is true beyond what the record says: report.py does not re-run any check or re-verify any evidence, and it does not validate the record. Unchecked rules and the coverage buckets do not enter the status, so a record can be `complete` with unchecked rules listed. The `status: complete` line is not a statement that the checks were sound; read the Audits and Unchecked rules sections with it.

## gen_fixtures.py

`python3 ${CLAUDE_SKILL_DIR}/scripts/gen_fixtures.py BASE_DIR OUT_DIR --models haiku,sonnet,opus` is a maintainer regression for validate.py: it mutates a valid record into schema-derived mutants and compares what validate.py catches with what the schema implies. OUT_DIR must not exist. BASE_DIR must validate first under the same `--models`; on the bundled example without `--models` it exits 2 (`baseline must validate before mutation: X08 ...`). It checks stated constraints only and cannot find constraints the schema omits. Needs `jsonschema` and `pyyaml`.

## Bundled files

`scripts/example/` is a valid record: `validate.py example --models haiku,sonnet,opus` exits 0, `coverage.py example` exits 0, and `report.py example` exits 0 with `status: complete`. `scripts/graph-record.schema.json` is the schema validate.py loads. The `test_*.py` files run with `python3 -m pytest -q` from `scripts/` (needs `pytest`).
