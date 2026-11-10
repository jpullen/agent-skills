# REPORT-SPEC: contract for `report.py`, the delivery-report generator

`report.py` reads a run record and prints the delivery report that the prompt's `<delivery>` section asks for (sources/graph-prompt-v3.5.md:122): what was checked, what passed with evidence, what failed, what is unresolved, any dissent with both positions, anything escalated, every unchecked rule, every assumption, and both audits, notes first, then counts. It ends with a status word and an exit code that say whether the record meets the Definition of Done.

Citation form: `(sources/<file>:<line>)` for a source line, `(gN)` for a given fact of this run, `[design]` for a clause no source or given states. Provenance: the `sources/` files and the `(gN)` givens were the inputs of the run that wrote this spec; they are not published, and the citations record provenance only. Framing assumptions u2 and a3 are the lead's framing, not sources; clauses that rest on them say so and are marked [design]. Terms: a "rule" is an entry of `rules.yaml` `rules`; a "row" is an entry of `checks.yaml` `rows`; a "subject" is the thing a row is about (C6); the "latest row" of a subject is its row with the highest `attempt` (C8); a "section" is one of the ten `## ` sections of the report (C20); "item lines" are the lines a section lists for its items.

## A. Command line and files

C1. The command line is `report.py RUN_DIR [--markdown]`; RUN_DIR is a directory holding a run record. Without `--markdown` the report is printed as text; with it, as markdown (section F). (g8) [design] for the positional RUN_DIR form, which follows the coverage.py bullet (sources/graph-record-README.md:8).

C2. Wrong usage (no RUN_DIR, more than one RUN_DIR, an unknown option, RUN_DIR not a directory) prints a line starting `usage:` to stderr, prints nothing to stdout, and exits 2. (g2, sources/graph-record-README.md:7)

C3. The program reads exactly four files from RUN_DIR: `rules.yaml`, `checks.yaml` and `progress.yaml` through coverage.py's `load_record` (C15), and `framing.yaml` (for Assumptions, C17) with PyYAML. It does not read `graph.yaml` or `lessons.yaml`: the node states the status needs are the `progress.graph` lists (C26). (g5, g6) [design] for not reading `graph.yaml`.

C4. A parse error prints a line starting `usage:` to stderr naming the cause, prints nothing to stdout, and exits 2. A parse error is any of: `load_record` raising its `ParseError` (a missing or malformed `rules.yaml`, `checks.yaml` or `progress.yaml`, a duplicate key); a missing or malformed `framing.yaml`; or a missing or mistyped field of the required set of C5. The case in which coverage.py would exit 2 on the same directory is a parse error here too, so report.py exits 2 (framing assumption a3). (g2, sources/graph-record-README.md:7) [design] for the framing.yaml and required-field causes and for a3.

C5. The required set, the fields that decide a count or the status: for every row, `subject` (a mapping whose `kind` is `node`, `acceptance` or `integration`, with `node` and `check` for kind `node` and `item` for kind `acceptance`), an integer `attempt`, and a `verdict` in the schema's vocabulary `pass`, `fail`, `unresolved`, `void`, `dissent`, `escalated`; in `progress`, `graph` with lists `running`, `failed`, `blocked`, `dissent`, `escalated`, `not_started`, `audits.wellformed.exit_code`, `audits.evidence` with `rows`, `miscited`, `unfound`, `verdict` and a list `notes`, `next_action.kind`, and a list `assumptions`; in `framing`, a list `assumptions`. Fields that only supply display detail (`evidence`, `dissent`, `usage` and its members, `reserve_runs`, `unchecked_rules`) are optional: an absent one prints as empty, and an absent `reserve_runs` is no entries. (sources/schema.json:74-82, sources/schema.json:834-858, sources/schema.json:936-939, sources/schema.json:1708-1743, sources/schema.json:1889-1990, sources/schema.json:2162-2213) [design] for which fields are required and for the optional fields printing empty.

## B. Subjects and verdicts

C6. A subject is identified by the fields the subject mapping gives for its kind: (kind `node`, `node`, `check`), or (kind `acceptance`, `item`), or (kind `integration`). Two rows of the same identity are the same subject; rows of different identities are different subjects. (g4, sources/schema.json:834-858)

C7. The subject is shown as `node:<node>/<check>`, `acceptance:<item>` or `integration`. (g4) [design] for the spelling.

C8. Each subject is counted at its latest row, the row with the highest `attempt`; the verdict, evidence and dissent used for it are that row's, and no earlier row is listed or counted. Two rows with the same subject and attempt cannot occur in a valid record (sources/schema.json:2840); if they do, the later one in `checks.yaml` is the latest. (g4) [design] for the tie.

C9. Membership: Checked holds every subject that has at least one row. Passed, Failed, Unresolved, Dissent and Escalated hold the subjects whose latest verdict is `pass`, `fail`, `unresolved`, `dissent` and `escalated` respectively; a latest verdict `void` puts the subject under Unresolved. Every subject is therefore in Checked and in exactly one of the other five. (g4, sources/schema.json:74-82)

C10. Within each verdict section the subjects are listed in the order in which they first appear in `checks.yaml`. (g4) [design] for the order.

C11. A subject line in Checked, Unresolved and Escalated is `<subject> #<attempt>`, with the subject of C7 and the attempt of its latest row. (g4)

C12. A Passed line is `<subject> #<attempt> | <evidence kind>`, the evidence kind being the `evidence.kind` of the latest row (`exec`, `location`, `excerpt` or `carried`). (g4, sources/schema.json:1111-1118) [design] for the ` | ` separator.

C13. A Failed line is `<subject> #<attempt> | <excerpt>`, the excerpt being the first 100 characters of the `excerpt` of the first entry of the latest row's `evidence.sections` whose `verdict` is `fail`, with each newline replaced by a space before the cut. When the row has no such entry the excerpt is empty and the line is `<subject> #<attempt> | ` with the separator kept. (g4, sources/schema.json:1138-1163) [design] for the newline handling and for the empty case.

C14. A Dissent line is `<subject> #<attempt> | <first position> | <second position>`. The first position is the `excerpt` of the entry of the latest row's `evidence.sections` whose `section` equals `dissent.section`, empty if there is none; the second is `dissent.reviewer_excerpt`. Each has newlines replaced by spaces and is not cut. (sources/graph-prompt-v3.5.md:122, sources/schema.json:1263-1282) [design] for which two excerpts are the two positions (framing assumption u2, the lead's framing, not a source line) and for the layout.

## C. The other sections

C15. Unchecked rules is obtained by importing `analyse` and `load_record` from `coverage.py` in the same directory as `report.py`, calling `load_record(RUN_DIR)` and then `analyse` on what it returns; the section holds the entries of `analyse`'s first result whose bucket is `unchecked` or `uncovered`, in the order `analyse` gives them. Neither function is reimplemented. (g5, sources/graph-prompt-v3.5.md:103)

C16. An Unchecked rules line is the text-mode rule line of coverage.py: `<rule id><TAB><bucket>` for an `uncovered` rule, and `<rule id><TAB>unchecked<TAB><reason>` for an `unchecked` rule, the reason being the string `analyse` returns, with newlines already replaced by spaces. Rules in the `exercised` bucket are not listed. (g5, `COVERAGE-SPEC.md` lines 51-57)

C17. Assumptions lists first the entries of `framing.yaml` `assumptions`, in file order, as `framing <id>: <text>`, then the entries of `progress.yaml` `assumptions`, in file order, as `progress <id>: <assumed>`; a progress entry has no `text` field, and its `assumed` field is the text. Newlines in the text are replaced by spaces. (g6, sources/schema.json:1756-1774, sources/schema.json:2480-2502) [design] for the `framing`/`progress` prefixes, the colon layout and the use of `assumed`.

C18. Audits holds, in this order and one per line: each note of the evidence audit as `note: <text>`, in file order, newlines replaced by spaces; then the counts as `evidence rows: <n>`, `evidence miscited: <n>`, `evidence unfound: <n>`, `evidence verdict: <word>`; then `wellformed exit code: <n>`. The notes come before the counts. (g6, sources/graph-prompt-v3.5.md:122, sources/schema.json:1897-1915, sources/schema.json:1962-1986) [design] for the label wording.

C19. Usage holds `consumed: <v>`, `limit: <v>`, `unit: <v>`, in that order, then one line per entry of `progress.usage.reserve_runs`, in file order, as `reserve: <kind>` followed by ` node=<node>`, ` attempt=<n>` and ` audit=<audit>` for each of those fields the entry has, in that order. Each value is printed as recorded, with nothing computed or estimated. (g6, sources/graph-prompt-v3.5.md:122, sources/schema.json:2038-2048, sources/schema.json:2058-2153) [design] for the line layout.

## D. Report structure

C20. The report has exactly ten sections, in this order, each beginning with a line `## <Heading>`: Checked, Passed, Failed, Unresolved, Dissent, Escalated, Unchecked rules, Assumptions, Audits, Usage. No other line of the report begins with `## `. (g3)

C21. Immediately after each `## <Heading>` line comes a line `count: <N>`, N being a non-negative integer written in decimal. (g8)

C22. What `count:` counts: in Checked, Passed, Failed, Unresolved, Dissent and Escalated, the subjects listed; in Unchecked rules, the rules listed; in Assumptions, the framing assumptions plus the progress assumptions; in Audits, the notes of the evidence audit; in Usage, the reserve entries. In text mode each of the first eight sections has N item lines after its `count:` line. (g8, g4, g5, g6)

C23. The last line of the report is `status: complete` or `status: partial`, after the Usage section; nothing follows it. A blank line precedes each `## ` heading after the first and precedes the status line. (g3) [design] for the blank lines.

C24. The text the program itself writes (headings, labels, status words) never contains the word `proven`. (sources/graph-prompt-v3.5.md:122)

## E. Status and exit codes

C25. The status is `complete` only when all four of C26 to C29 hold; otherwise it is `partial`. (g2)

C26. Condition nodes: every node is accepted, tested as `progress.graph` lists `running`, `failed`, `blocked`, `dissent`, `escalated` and `not_started` all being empty (the lists partition the nodes, so no node is then outside `accepted`). (g2, sources/schema.json:2828)

C27. Condition subjects: every subject's latest-attempt verdict is `pass`, that is, the Passed count equals the Checked count and Failed, Unresolved, Dissent and Escalated are all empty. (g2, g4)

C28. Condition audits: `progress.audits.wellformed.exit_code` is 0 and `progress.audits.evidence.verdict` is `pass`; any other verdict, including `not_run` and `fail`, fails the condition. (g2, sources/schema.json:1905-1907, sources/schema.json:1974-1980)

C29. Condition next action: `progress.next_action.kind` is `delivery`. (g2, sources/schema.json:2169-2175)

C30. The Unchecked rules section and the coverage buckets do not enter the status or the exit code: a record may complete with unchecked rules. (g2, sources/graph-prompt-v3.5.md:103)

C31. Exit 0 when the status is `complete`; exit 1 when it is `partial`, the whole report still being printed to stdout. (g2)

C32. Exit 2 on a usage error (C2) or a parse error (C4); nothing is written to stdout, so the report is built in full before any of it is printed. (g2, sources/graph-record-README.md:7) [design] for building the whole report first.

## F. Markdown rendering

C33. With `--markdown` the report has the same ten `## <Heading>` lines in the same order, each followed by its `count:` line, the same counts as in text mode, and the same final `status:` line. (g8, g3)

C34. With `--markdown`, a section whose `count:` is above 0 renders its items as a table: a header row `| <col> | <col> | ... |`, a separator row `| --- | --- | ... |`, and one row per item. A section whose `count:` is 0 prints no table, except that Audits and Usage always print a table, because they also hold values (C37). (g8) [design] for the table shape and for the exception.

C35. The columns of the verdict sections: Checked, Unresolved and Escalated `| Subject | Attempt |`; Passed `| Subject | Attempt | Evidence |`; Failed `| Subject | Attempt | Excerpt |`; Dissent `| Subject | Attempt | Position | Dissent |`. The Subject cell is the subject of C7 and the Attempt cell the number alone. (g8) [design] for the column headings.

C36. The columns of Unchecked rules `| Rule | Bucket | Reason |`, with an empty Reason cell for `uncovered`; of Assumptions `| Source | Id | Text |`, with the Source cell `framing` or `progress`. (g8) [design] for the column headings.

C37. Audits and Usage are tables `| Item | Value |`. Audits has one row per line of C18, the Item cell being the label before the colon (`note`, `evidence rows`, `evidence miscited`, `evidence unfound`, `evidence verdict`, `wellformed exit code`) and the Value cell the rest of the line. Usage has one row per line of C19, the Item cell being `consumed`, `limit`, `unit` or `reserve`, and the Value cell the rest of the line. (g8) [design] for the layout.

C38. In a markdown cell a `|` is written `\|` and a newline as a space, so every row stays on one line. (g8) [design]

## G. Read-only, dependencies, location

C39. Read-only: the program writes nothing under RUN_DIR, creates no file there, and opens its four files for reading only. (g1, sources/graph-record-README.md:8)

C40. Dependencies: Python 3 standard library and PyYAML only, plus `coverage.py` from the same directory (C15); no import of `validate.py` or of `jsonschema`. (g7, g5)

C41. Files: the deliverable lives in `graph-record/` beside `validate.py` and `coverage.py` as `report.py`, `test_report.py` and this `REPORT-SPEC.md`, with one bullet in the kit's graph-record README after the coverage.py bullet (that README is not published; the published equivalent is the report.py section of `SKILL.md`). (g9)
