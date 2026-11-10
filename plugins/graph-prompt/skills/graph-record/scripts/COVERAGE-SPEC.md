# COVERAGE-SPEC: contract for `coverage.py`, the rule-coverage reporter

`coverage.py` reads a run record and reports, for each rule that concerns the deliverable, whether some acceptance check exercises it, whether it was listed as unchecked with a reason, or whether it is neither.

Citation form: `(sources/<file>:<line>)` for a source line, `(gN)` for a given fact of this run, `[design]` for a clause no source or given states. Provenance: the `sources/` files and the `(gN)` givens were the inputs of the run that wrote this spec; they are not published, and the citations record provenance only. Framing assumptions a1 and a2 are the lead's framing, not sources; clauses that rest on them say so and are marked [design]. Terms: a "rule" is an entry of `rules.yaml` `rules`; a "row" is an entry of `checks.yaml` `rows`; X32 and X09 are the cross-file rules of the schema's `x-crossfile` list.

## A. Command line and files

C1. The command line is `coverage.py RUN_DIR [--markdown]`; RUN_DIR is a directory holding a run record. (g5, g6)

C2. Wrong usage (no RUN_DIR, more than one RUN_DIR, an unknown option, RUN_DIR not a directory) prints a line starting `usage:` to stderr and exits 2. (g2) The `usage:` prefix on stderr follows validate.py's practice (sources/validate.py:465).

C3. The reporter reads exactly three files from RUN_DIR: `rules.yaml`, `checks.yaml` and `progress.yaml`, each named `<name>.yaml` as validate.py names its record files. (sources/validate.py:42)

C4. A missing file among the three, a YAML syntax error, a duplicate mapping key, or a top-level shape that is not the one the schema gives (`rules.rules` a list of rule entries, `checks.rows` a list of rows, `progress` a mapping) is a parse error: a line starting `usage:` on stderr naming the cause, exit 2, nothing on stdout. (g2) The duplicate-key refusal follows the loader validate.py uses (sources/validate.py:31). [design] for treating a missing file as a parse error.

C5. The reporter does not validate the record against the schema and does not evaluate any rule other than X32 and the X09 condition of C16; it reads only the fields named in this contract. [design]

## B. Which rules are reported

C6. A deliverable rule is a rule whose `concerns` list includes `deliverable`; a rule with no `concerns` is not a deliverable rule. (sources/validate.py:436) The schema's `concerns` values are `deliverable`, `graph`, `checks`, `progress`. (sources/schema.json:2731)

C7. Every deliverable rule gets exactly one rule line (text) or one table row (markdown), in the order the rules appear in `rules.yaml`, and is counted in exactly one of the three buckets. (g5) [design] for the order and for "exactly one", which makes the three counts sum to the number of deliverable rules.

C8. A rule that is not a deliverable rule gets no rule line and no table row, counts in no summary bucket, and is listed in a separate manual section after the summary line (C22, C23). (framing assumption a1) [design] (a1 is the lead's framing and is not a source line).

## C. The coverage relation

C9. The rows whose `exercises` the reporter reads are acceptance rows only, those with `subject.kind` equal to `acceptance`; `exercises` on a row of any other subject kind is ignored. This is the person's answer to u1. (g7) The schema describes the field as "Acceptance rows only." (sources/schema.json:1261) and the graph-record README, which was not published, repeated that `exercises` is a row field on acceptance rows only (sources/graph-record-README.md:18); the published equivalent is the coverage.py section of `SKILL.md`, in the parent directory.

C10. Bucket `exercised`: a deliverable rule whose id appears in the `exercises` list of at least one acceptance row. (g5, g7) The attempt and verdict of the row do not matter to the bucket (validate.py counts rows without regard to either, sources/validate.py:428). [design] for that last point. The schema requires every acceptance row to carry `exercises`, an empty list meaning acceptance only. (sources/schema.json:1581, sources/schema.json:1261)

C11. Bucket `unchecked`: a deliverable rule that is not exercised (C10) and whose id appears in `progress.unchecked_rules`; each entry there carries an `id` and a `reason`. (g5, sources/schema.json:1783) The schema describes the list as rules that no check exercises, listed before approval with the reason. (sources/schema.json:1783)

C12. Bucket `uncovered`: a deliverable rule that is not exercised (C10) and not in `progress.unchecked_rules`. This is the X32 finding "concerns the deliverable but no checks row exercises it and progress.unchecked_rules does not list it". (sources/validate.py:436-437, sources/schema.json:2850)

C13. Error condition 1: an id in `progress.unchecked_rules` that is not a rule id of `rules.yaml` is a finding, printed as `X32 progress.unchecked_rules: <id> is not a rules id`; the id is counted in no bucket. (sources/validate.py:430-432, sources/schema.json:2850)

C14. Error condition 2: an id in `progress.unchecked_rules` that is a rule id and is also named in the `exercises` of an acceptance row is a finding, printed as `X32 progress.unchecked_rules: <id> is both exercised and listed as unchecked`. The rule, if deliverable, is bucketed `exercised` (C10 takes precedence over C11). (sources/validate.py:433-434, sources/schema.json:2850) [design] for the bucket chosen; validate.py counts such a rule as exercised for the uncovered test (sources/validate.py:436).

C15. Unchecked-before-approval: a rule with no exercising check is meant to be listed in `progress.unchecked_rules` with its reason before approval, and the list is reported at delivery; the reporter is that delivery-time report, and reads the list as it stands in `progress.yaml` whatever the stage of the run, without checking that approval has occurred. (sources/graph-prompt-v3.5.md:103, sources/graph-prompt-v3.5.md:122) [design] for "without checking that approval has occurred".

C16. Condition X09: an id in the `exercises` of an acceptance row that is not a rule id is a finding, printed as `X09 <item>#<attempt>: exercises <id> not in rules`; the id names no rule and so appears in no bucket. (sources/validate.py:208-210, sources/schema.json:2827) The finding does not change the exit code (C27), because exit 0 is defined by X32 alone. (g2) [design] for confining the check to acceptance rows (C9) and for leaving the exit code unchanged.

C17. The u1 decision: whether `exercises` counts on acceptance rows only or on every row is settled as acceptance rows only. (g7) validate.py's X32 also builds its exercised set from acceptance rows only (sources/validate.py:428), so the reporter and validate.py agree on this point (C31).

## D. Text report

C18. By default the reporter prints a text report to stdout: first one rule line per deliverable rule (C7), then the summary line (C22), then the findings (C26) if any, then the manual section (C23) if any. (g5) [design] for the order of the last two.

C19. Every rule line begins with the rule id, one TAB character, then the bucket word, which is exactly one of `exercised`, `unchecked`, `uncovered`: `<rule id><TAB><bucket>`. (g8)

C20. After the bucket word a rule line continues with a TAB and a detail field:
- `exercised`: the exercising rows, comma-separated, each `<item>#<attempt>=<verdict>`, one per acceptance item that exercises the rule, ordered by first appearance in `checks.yaml`; `<item>` is the row's `subject.item`, and `<attempt>` and `<verdict>` are those of that item's newest row (highest attempt), not of the older row that named the rule. (g5)
- `unchecked`: the reason string from `progress.unchecked_rules`, with newlines in it replaced by spaces. (g5)
- `uncovered`: no detail field and no second TAB. (g5, g8)
`<item>`, `<attempt>` and `<verdict>` are the schema's `subject.item`, `attempt` and `verdict` fields. (sources/schema.json:854, sources/schema.json:936, sources/schema.json:74-82) [design] for the field layout, for the separators, and for taking the item's newest attempt (framing assumption a2, the lead's framing, not a source line).

C21. A rule line that carries a detail field is not split across lines; each rule occupies one line. (g5)

C22. The summary line begins `summary:` and states the three counts in this order: `summary: exercised=<n> unchecked=<n> uncovered=<n>`; the three numbers add up to the number of deliverable rules. (g5, g8) [design] for the `name=count` spelling.

C23. The manual section lists the rules that are not deliverable rules (C8): a first line `manual (not counted in the summary):`, then one line per such rule, indented by two spaces, as `  <rule id> <concerns joined by comma>`; with no such rule the section is omitted. The indent keeps these lines from matching the rule-line shape of C19. (g8) [design] (framing assumption a1; the section's wording is the reporter's own).

## E. Markdown report

C24. With `--markdown` the reporter prints the same content as one table: a header row `| Rule | Bucket | Detail |`, a separator row, and one row per deliverable rule (C7) that begins `| <rule id> |`, giving the bucket word and the detail field of C20 (an empty cell for `uncovered`). (g5, g8) [design] for the header wording and column layout.

C25. After the table, `--markdown` prints the summary line of C22 unchanged, then the findings (C26) and the manual section (C23) in the same text form; `--markdown` changes the presentation of the rule lines only. (g5) [design] for the placement of the three after the table.

## F. Findings and exit codes

C26. A finding is a line `<rule> <subject>: <message>` printed to stdout, in the form validate.py prints. (sources/validate.py:5-6, sources/validate.py:484) The findings are: one `X32 rules <id>: concerns the deliverable but no checks row exercises it and progress.unchecked_rules does not list it` for each uncovered rule (C12), the two X32 error conditions (C13, C14), and the X09 findings (C16). All findings are printed; the reporter does not stop at the first.

C27. Exit 0 when X32 holds on the record: no deliverable rule is uncovered and neither error condition (C13, C14) occurs. (g2, sources/graph-record-README.md:7) The reporter exits 0 even when the manual section is non-empty or X09 findings exist (C16).

C28. Exit 1 when X32 does not hold: at least one uncovered rule (C12), or an error condition of C13 or C14; the findings are printed (C26). (g2, sources/graph-record-README.md:7)

C29. Exit 2 on usage error or parse error (C2, C4); stdout stays empty. (g2, sources/graph-record-README.md:7)

C30. Read-only: the reporter writes nothing under RUN_DIR, creates no file there, and opens its three files for reading only. (g1)

## G. Agreement with validate.py and dependencies

C31. No divergence on `exercises`: validate.py's X32 builds its exercised set from acceptance rows only (sources/validate.py:428), as the reporter does (C9). A rule named only in the `exercises` of a non-acceptance row is not exercised for either. (g7) The schema's field description and the kit's graph-record README (not published; the published equivalent is the coverage.py section of `SKILL.md`) state acceptance rows only (sources/schema.json:1261, sources/graph-record-README.md:18).

C32. Agreement property: on `example/` and on records generated from it, the set of rule ids the reporter buckets as `uncovered` equals the set of rule ids validate.py reports as uncovered by X32, no more and no fewer. (g3) The reporter's exit code is not claimed to equal validate.py's on those records, since validate.py also evaluates the other rules and the schema. [design] for the last clause.

C33. Dependencies: Python 3 standard library and PyYAML only; no other third-party module, and no import of `validate.py` or of `jsonschema`. (g4)

C34. Files: the deliverable lives in `graph-record/` beside validate.py as `coverage.py`, `test_coverage.py`, this `COVERAGE-SPEC.md`, and a paragraph in the kit's graph-record README (not published; the published equivalent is the coverage.py section of `SKILL.md`). (g6)
