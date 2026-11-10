"""Tests for report.py, the delivery-report generator, to the contract REPORT-SPEC.md.

Run: python -m pytest -q test_report.py

Each test is named test_cNN_<behaviour> for the REPORT-SPEC clause C<NN> it exercises and checks one
element of that clause with its own fixture, so that removing that element from report.py fails it.
Fixtures are copies of example/ made in tmp_path and mutated there; example/ is only read. report.py runs as a subprocess so that exit codes, stdout and stderr are
observable. Givens cited in docstrings: (g1) read-only, (g2) exit codes, (g3) section order, (g4)
latest-attempt verdicts, (g5) unchecked rules from coverage.py, (g6) audits, assumptions and usage,
(g8) counts and markdown.
"""
import ast
import pathlib
import shutil
import subprocess
import sys

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
EXAMPLE = HERE / "example"
REPORT = HERE / "report.py"
COVERAGE = HERE / "coverage.py"

HEADINGS = ["Checked", "Passed", "Failed", "Unresolved", "Dissent", "Escalated",
            "Unchecked rules", "Assumptions", "Audits", "Usage"]
TEXT_ITEM_SECTIONS = HEADINGS[:8]
GRAPH_LISTS = ["running", "failed", "blocked", "dissent", "escalated", "not_started"]
PARTIAL_VERDICTS = ["fail", "unresolved", "void", "dissent", "escalated"]

BUILDER = "builder says the usage section is complete"
REVIEWER = "reviewer says the usage section is missing reserve runs"
FAIL_TEXT = "usage check failed: the reviewer found a missing section"


# fixtures and helpers -------------------------------------------------------------

def make_record(tmp_path):
    d = tmp_path / "rec"
    shutil.copytree(EXAMPLE, d)
    return d


def read_yaml(d, name):
    return yaml.safe_load((d / f"{name}.yaml").read_text(encoding="utf-8"))


def write_yaml(d, name, data):
    (d / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def edit_checks(d, fn):
    data = read_yaml(d, "checks")
    fn(data["rows"])
    write_yaml(d, "checks", data)


def edit_progress(d, fn):
    data = read_yaml(d, "progress")
    fn(data)
    write_yaml(d, "progress", data)


def edit_rules(d, fn):
    data = read_yaml(d, "rules")
    fn(data["rules"])
    write_yaml(d, "rules", data)


def edit_framing(d, fn):
    data = read_yaml(d, "framing")
    fn(data)
    write_yaml(d, "framing", data)


def acceptance_row(item, attempt, verdict, evidence_kind="exec"):
    return {
        "subject": {"kind": "acceptance", "item": item}, "attempt": attempt,
        "requirement": f"item {item}", "type": "exec", "verdict": verdict,
        "evidence": {"kind": evidence_kind, "command": "bash integration.sh", "expected_exit": 0,
                     "actual_exit": 0, "output": f"{item} output"},
    }


def node_row(node, check, verdict, sections=None, attempt=1):
    return {
        "subject": {"kind": "node", "node": node, "check": check}, "attempt": attempt,
        "requirement": f"{check} holds", "type": "review", "verdict": verdict,
        "evidence": {"kind": "excerpt", "sections": sections or []},
    }


def failing_row(node, check, excerpt, attempt=1):
    return node_row(node, check, "fail", [{"section": "usage", "verdict": "fail", "excerpt": excerpt}],
                    attempt=attempt)


def dissent_row(node, check, attempt=1, builder=None, reviewer=None):
    return {
        "subject": {"kind": "node", "node": node, "check": check}, "attempt": attempt,
        "requirement": "usage section complete", "type": "review", "verdict": "dissent",
        "evidence": {"kind": "excerpt", "sections": [
            {"section": "usage", "verdict": "pass", "excerpt": builder or f"builder says {check} is complete"}]},
        "dissent": {"section": "usage", "reviewer_excerpt": reviewer or f"reviewer says {check} is not",
                    "reason": "the reserve lines are absent"},
    }


def rich(tmp_path):
    """A record in which every section has items, each subject at a distinct attempt.

    checks.yaml rows (index: subject, latest attempt, latest verdict):
      0 node:g1/g1-gate #2 pass   1 node:g3/g3-review #1 pass   2 acceptance:c1 #3 pass
      3 integration #4 pass       4 node:g2/g2-gate #5 fail (excerpt in its usage section)
      5 acceptance:c2 #6 void (Unresolved)   6 acceptance:c3 #7 escalated
      7 node:g4/g4-review #8 dissent (builder and reviewer positions)
    rules.yaml: s-namematch and s-verdicts are exercised; s-gap is uncovered; s-extra is unchecked.
    progress.yaml: two reserve entries, one with a node and one with an audit.
    """
    d = make_record(tmp_path)

    def rows_edit(rows):
        rows[0]["attempt"] = 2
        rows[2]["attempt"] = 3
        rows[3]["attempt"] = 4
        rows.extend([
            failing_row("g2", "g2-gate", FAIL_TEXT, attempt=5),
            acceptance_row("c2", 6, "void"),
            acceptance_row("c3", 7, "escalated"),
            dissent_row("g4", "g4-review", attempt=8, builder=BUILDER, reviewer=REVIEWER),
        ])
    edit_checks(d, rows_edit)
    edit_rules(d, lambda rules: rules.extend([
        {"id": "s-gap", "spec": "graph-prompt-v2.7.md", "rule": "a deliverable rule no row exercises",
         "section": "layer_5_gates", "quote": "a deliverable rule", "concerns": ["deliverable"]},
        {"id": "s-extra", "spec": "graph-prompt-v2.7.md", "rule": "a rule read by hand",
         "section": "layer_5_gates", "quote": "a rule read by hand", "concerns": ["deliverable"]},
    ]))

    def progress(p):
        p["unchecked_rules"] = [{"id": "s-extra", "reason": "needs a live endpoint"}]
        p["usage"]["reserve_runs"] = [
            {"kind": "correction_return", "node": "g2"},
            {"kind": "audit", "audit": "evidence"},
        ]
    edit_progress(d, progress)
    return d


RICH_TEXT = {
    "Checked": ["node:g1/g1-gate #2", "node:g3/g3-review #1", "acceptance:c1 #3", "integration #4",
                "node:g2/g2-gate #5", "acceptance:c2 #6", "acceptance:c3 #7", "node:g4/g4-review #8"],
    "Passed": ["node:g1/g1-gate #2 | exec", "node:g3/g3-review #1 | excerpt", "acceptance:c1 #3 | exec",
               "integration #4 | exec"],
    "Failed": ["node:g2/g2-gate #5 | " + FAIL_TEXT],
    "Unresolved": ["acceptance:c2 #6"],
    "Dissent": ["node:g4/g4-review #8 | " + BUILDER + " | " + REVIEWER],
    "Escalated": ["acceptance:c3 #7"],
}

RICH_MARKDOWN = {
    "Checked": ["| node:g1/g1-gate | 2 |", "| node:g3/g3-review | 1 |", "| acceptance:c1 | 3 |",
                "| integration | 4 |", "| node:g2/g2-gate | 5 |", "| acceptance:c2 | 6 |",
                "| acceptance:c3 | 7 |", "| node:g4/g4-review | 8 |"],
    "Passed": ["| node:g1/g1-gate | 2 | exec |", "| node:g3/g3-review | 1 | excerpt |",
               "| acceptance:c1 | 3 | exec |", "| integration | 4 | exec |"],
    "Failed": ["| node:g2/g2-gate | 5 | " + FAIL_TEXT + " |"],
    "Unresolved": ["| acceptance:c2 | 6 |"],
    "Dissent": ["| node:g4/g4-review | 8 | " + BUILDER + " | " + REVIEWER + " |"],
    "Escalated": ["| acceptance:c3 | 7 |"],
    "Unchecked rules": ["| s-gap | uncovered |  |", "| s-extra | unchecked | needs a live endpoint |"],
    "Assumptions": ["| framing | a1 | the record format is what the spec states |", "| progress | a1 | yes |"],
}

HEADER_ROWS = {
    "Checked": "| Subject | Attempt |",
    "Passed": "| Subject | Attempt | Evidence |",
    "Failed": "| Subject | Attempt | Excerpt |",
    "Unresolved": "| Subject | Attempt |",
    "Dissent": "| Subject | Attempt | Position | Dissent |",
    "Escalated": "| Subject | Attempt |",
    "Unchecked rules": "| Rule | Bucket | Reason |",
    "Assumptions": "| Source | Id | Text |",
    "Audits": "| Item | Value |",
    "Usage": "| Item | Value |",
}


def two_each(tmp_path):
    """Two subjects in each of Failed, Unresolved, Dissent and Escalated, appended to example/."""
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([
        failing_row("g2", "g2-a", "first fail"),
        failing_row("g2", "g2-b", "second fail"),
        acceptance_row("c2", 1, "void"),
        acceptance_row("c3", 1, "unresolved"),
        dissent_row("g4", "g4-a"),
        dissent_row("g4", "g4-b"),
        acceptance_row("c4", 1, "escalated"),
        acceptance_row("c5", 1, "escalated"),
    ]))
    return d


def audit_values(tmp_path):
    """example/ with distinct audit values, so that no two labels can swap unseen."""
    d = make_record(tmp_path)
    edit_progress(d, lambda p: (
        p["audits"]["evidence"].update(rows=9, miscited=2, unfound=5, verdict="fail"),
        p["audits"]["wellformed"].update(exit_code=3)))
    return d


def empty_record(tmp_path):
    """No rows, no rules and no assumptions: every item section is empty."""
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.clear())
    write_yaml(d, "rules", {"rules": []})
    edit_framing(d, lambda f: f.update(assumptions=[]))
    edit_progress(d, lambda p: p.update(assumptions=[]))
    return d


def run_report(*argv):
    return subprocess.run([sys.executable, str(REPORT), *map(str, argv)], capture_output=True, text=True)


def run(d, *extra):
    return run_report(d, *extra)


def assert_parse_error(res):
    assert res.returncode == 2
    assert any(line.startswith("usage:") for line in res.stderr.splitlines())


def split_sections(text):
    """Return (heading order, {heading: lines after the heading line up to the next heading})."""
    order, bodies, cur = [], {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:]
            order.append(cur)
            bodies[cur] = []
        elif cur is not None:
            bodies[cur].append(line)
    return order, bodies


def section(text, heading):
    return split_sections(text)[1][heading]


def count_of(body):
    assert body and body[0].startswith("count: "), f"no count line in {body[:1]}"
    return int(body[0][len("count: "):])


def items_of(body):
    out = []
    for line in body[1:]:
        if line == "" or line.startswith("status:"):
            break
        out.append(line)
    return out


def table_of(body):
    """The markdown table lines of a section body: header row, separator row, item rows."""
    return [line for line in body[1:] if line.startswith("|")]


def last_line(text):
    return text.splitlines()[-1]


# command line and usage errors (C1, C2, C3) ------------------------------------------

def test_c01_markdown_flag_selects_table_output(tmp_path):
    d = make_record(tmp_path)
    text_lines = run(d).stdout.splitlines()
    md_lines = run(d, "--markdown").stdout.splitlines()
    assert "| Subject | Attempt |" not in text_lines
    assert "| Subject | Attempt |" in md_lines


def test_c02_no_run_dir_is_usage_error():
    assert_parse_error(run_report())


def test_c02_two_run_dirs_is_usage_error(tmp_path):
    d = make_record(tmp_path)
    assert_parse_error(run_report(d, d))


def test_c02_unknown_option_is_usage_error(tmp_path):
    d = make_record(tmp_path)
    assert_parse_error(run(d, "--bogus"))


def test_c02_run_dir_not_a_directory_is_usage_error(tmp_path):
    assert_parse_error(run_report(tmp_path / "absent"))


def test_c02_usage_error_prints_nothing_to_stdout():
    assert run_report().stdout == ""


def test_c03_graph_yaml_is_not_read(tmp_path):
    d = make_record(tmp_path)
    baseline = run(d)
    (d / "graph.yaml").unlink()
    res = run(d)
    assert res.returncode == 0
    assert res.stdout == baseline.stdout


def test_c03_lessons_yaml_is_not_read(tmp_path):
    d = make_record(tmp_path)
    baseline = run(d)
    (d / "lessons.yaml").unlink()
    res = run(d)
    assert res.returncode == 0
    assert res.stdout == baseline.stdout


# parse errors and required fields (C4, C5, C32) ----------------------------------------

def test_c04_missing_checks_file_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "checks.yaml").unlink()
    res = run(d)
    assert_parse_error(res)
    assert "checks.yaml" in res.stderr


def test_c04_yaml_syntax_error_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "rules.yaml").write_text("rules: [unclosed\n", encoding="utf-8")
    assert_parse_error(run(d))


def test_c04_duplicate_key_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "progress.yaml").write_text("enforcement: {kind: a}\nenforcement: {kind: b}\n", encoding="utf-8")
    res = run(d)
    assert_parse_error(res)
    assert "duplicate" in res.stderr


def test_c04_rules_shape_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    write_yaml(d, "rules", {"rules": "not a list"})
    assert_parse_error(run(d))


def test_c04_missing_framing_file_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "framing.yaml").unlink()
    assert_parse_error(run(d))


def test_c04_malformed_framing_yaml_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "framing.yaml").write_text("assumptions: [unclosed\n", encoding="utf-8")
    assert_parse_error(run(d))


def test_c04_parse_error_prints_nothing_to_stdout(tmp_path):
    d = make_record(tmp_path)
    (d / "checks.yaml").unlink()
    assert run(d).stdout == ""


def test_c05_progress_without_evidence_audit_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"].pop("evidence"))
    assert_parse_error(run(d))


def _drop(*path):
    def fn(p):
        node = p
        for key in path[:-1]:
            node = node[key]
        node.pop(path[-1])
    return fn


def _set(*path_and_value):
    *path, value = path_and_value

    def fn(p):
        node = p
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return fn


PROGRESS_MISSING = {
    "graph": _drop("graph"),
    **{f"graph.{name}": _drop("graph", name) for name in GRAPH_LISTS},
    "audits.wellformed.exit_code": _drop("audits", "wellformed", "exit_code"),
    "audits.evidence.rows": _drop("audits", "evidence", "rows"),
    "audits.evidence.miscited": _drop("audits", "evidence", "miscited"),
    "audits.evidence.unfound": _drop("audits", "evidence", "unfound"),
    "audits.evidence.verdict": _drop("audits", "evidence", "verdict"),
    "audits.evidence.notes": _drop("audits", "evidence", "notes"),
    "next_action.kind": _drop("next_action", "kind"),
    "assumptions": _drop("assumptions"),
}

PROGRESS_MISTYPED = {
    **{f"graph.{name}": _set("graph", name, "g9") for name in GRAPH_LISTS},
    "audits.wellformed.exit_code": _set("audits", "wellformed", "exit_code", "0"),
    "audits.evidence.rows": _set("audits", "evidence", "rows", "three"),
    "audits.evidence.miscited": _set("audits", "evidence", "miscited", "none"),
    "audits.evidence.unfound": _set("audits", "evidence", "unfound", "none"),
    "audits.evidence.verdict": _set("audits", "evidence", "verdict", 5),
    "audits.evidence.notes": _set("audits", "evidence", "notes", "a note"),
    "next_action.kind": _set("next_action", "kind", 5),
    "assumptions": _set("assumptions", "yes"),
}


@pytest.mark.parametrize("field", list(PROGRESS_MISSING))
def test_c05_missing_required_progress_field_is_parse_error(tmp_path, field):
    d = make_record(tmp_path)
    edit_progress(d, PROGRESS_MISSING[field])
    res = run(d)
    assert_parse_error(res)
    assert field.split(".")[-1] in res.stderr


@pytest.mark.parametrize("field", list(PROGRESS_MISTYPED))
def test_c05_mistyped_required_progress_field_is_parse_error(tmp_path, field):
    d = make_record(tmp_path)
    edit_progress(d, PROGRESS_MISTYPED[field])
    res = run(d)
    assert_parse_error(res)
    assert field.split(".")[-1] in res.stderr


def test_c05_missing_framing_assumptions_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    edit_framing(d, lambda f: f.pop("assumptions"))
    assert_parse_error(run(d))


def test_c05_mistyped_framing_assumptions_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    edit_framing(d, lambda f: f.update(assumptions="yes"))
    assert_parse_error(run(d))


ROW_FAULTS = {
    "subject_absent": lambda rows: rows[0].pop("subject"),
    "subject_not_a_mapping": lambda rows: rows[0].update(subject="g1"),
    "subject_kind_absent": lambda rows: rows[0]["subject"].pop("kind"),
    "subject_kind_outside_vocabulary": lambda rows: rows[0]["subject"].update(kind="bogus"),
    "node_subject_without_node": lambda rows: rows[0]["subject"].pop("node"),
    "node_subject_without_check": lambda rows: rows[0]["subject"].pop("check"),
    "node_subject_mistyped_node": lambda rows: rows[0]["subject"].update(node=5),
    "acceptance_subject_without_item": lambda rows: rows[2]["subject"].pop("item"),
    "acceptance_subject_mistyped_item": lambda rows: rows[2]["subject"].update(item=5),
    "attempt_absent": lambda rows: rows[0].pop("attempt"),
    "attempt_a_string": lambda rows: rows[0].update(attempt="1"),
    "attempt_a_boolean": lambda rows: rows[0].update(attempt=True),
    "verdict_absent": lambda rows: rows[0].pop("verdict"),
    "verdict_outside_vocabulary": lambda rows: rows[0].update(verdict="maybe"),
}


@pytest.mark.parametrize("fault", list(ROW_FAULTS))
def test_c05_row_field_fault_is_parse_error(tmp_path, fault):
    d = make_record(tmp_path)
    edit_checks(d, ROW_FAULTS[fault])
    assert_parse_error(run(d))


def test_c05_integration_subject_needs_no_other_field(tmp_path):
    d = make_record(tmp_path)
    assert run(d).returncode == 0
    assert read_yaml(d, "checks")["rows"][3]["subject"] == {"kind": "integration"}


def test_c05_absent_evidence_prints_empty_kind(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows[3].pop("evidence"))
    res = run(d)
    assert res.returncode == 0
    assert "integration #1 |" in [line.rstrip() for line in items_of(section(res.stdout, "Passed"))]


def test_c05_absent_evidence_on_failed_row_prints_empty_excerpt(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[4].pop("evidence"))
    res = run(d)
    assert [line.rstrip() for line in items_of(section(res.stdout, "Failed"))] == ["node:g2/g2-gate #5 |"]


def test_c05_absent_dissent_prints_empty_positions(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[7].pop("dissent"))
    res = run(d)
    assert [line.rstrip() for line in items_of(section(res.stdout, "Dissent"))] == ["node:g4/g4-review #8 |  |"]


def test_c05_absent_usage_prints_empty_scalars(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p.pop("usage"))
    res = run(d)
    assert res.returncode == 0
    assert [line.rstrip() for line in items_of(section(res.stdout, "Usage"))] == [
        "consumed:", "limit:", "unit:"]


def test_c05_absent_usage_limit_prints_empty_limit(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["usage"].pop("limit"))
    res = run(d)
    assert res.returncode == 0
    assert [line.rstrip() for line in items_of(section(res.stdout, "Usage"))] == [
        "consumed: 7", "limit:", "unit: node_runs"]


def test_c05_absent_reserve_runs_is_no_entries(tmp_path):
    d = make_record(tmp_path)
    assert "reserve_runs" not in read_yaml(d, "progress")["usage"]
    body = section(run(d).stdout, "Usage")
    assert count_of(body) == 0
    assert not any(line.startswith("reserve:") for line in items_of(body))


def test_c32_late_parse_error_prints_nothing_to_stdout(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes="not a list"))
    assert run(d).stdout == ""


# subjects and latest attempt (C6 to C12) ---------------------------------------------

def test_c06_same_node_different_check_are_two_subjects(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(node_row("g1", "g1-second", "pass")))
    assert count_of(section(run(d).stdout, "Checked")) == 5


def test_c06_same_check_different_node_are_two_subjects(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(node_row("g5", "g3-review", "pass")))
    assert count_of(section(run(d).stdout, "Checked")) == 5


def test_c06_rows_of_one_acceptance_subject_counted_once(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(acceptance_row("c1", 2, "pass")))
    assert count_of(section(run(d).stdout, "Checked")) == 4


def test_c06_rows_of_the_integration_subject_counted_once(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(
        {"subject": {"kind": "integration"}, "attempt": 2, "requirement": "all acceptance items pass",
         "type": "exec", "verdict": "pass", "evidence": {"kind": "exec", "output": "all pass"}}))
    assert count_of(section(run(d).stdout, "Checked")) == 4


def test_c07_subject_spelling(tmp_path):
    d = make_record(tmp_path)
    items = items_of(section(run(d).stdout, "Checked"))
    assert sorted(items) == sorted([
        "node:g1/g1-gate #1", "node:g3/g3-review #1", "acceptance:c1 #1", "integration #1",
    ])


def test_c08_latest_attempt_is_the_highest_attempt(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(acceptance_row("c1", 2, "fail")))
    items = items_of(section(run(d).stdout, "Checked"))
    assert "acceptance:c1 #2" in items
    assert "acceptance:c1 #1" not in items


def test_c08_lower_attempt_later_in_file_does_not_win(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([acceptance_row("c1", 2, "fail"), acceptance_row("c1", 1, "pass")]))
    items = items_of(section(run(d).stdout, "Checked"))
    assert "acceptance:c1 #2" in items
    assert "acceptance:c1 #1" not in items


def test_c08_tie_on_attempt_takes_later_row(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(acceptance_row("c1", 1, "fail")))
    res = run(d)
    failed = items_of(section(res.stdout, "Failed"))
    assert any(line.startswith("acceptance:c1 #1 | ") for line in failed)
    assert not any(line.startswith("acceptance:c1 #1") for line in items_of(section(res.stdout, "Passed")))


def test_c08_failed_excerpt_is_the_latest_rows(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([
        failing_row("g2", "g2-gate", "old excerpt", attempt=1),
        failing_row("g2", "g2-gate", "new excerpt", attempt=2),
    ]))
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #2 | new excerpt"]


def test_c08_passed_evidence_kind_is_the_latest_rows(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([
        acceptance_row("c9", 1, "pass", evidence_kind="location"),
        acceptance_row("c9", 2, "pass", evidence_kind="carried"),
    ]))
    assert "acceptance:c9 #2 | carried" in items_of(section(run(d).stdout, "Passed"))


def test_c08_dissent_first_position_is_the_latest_rows(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([
        dissent_row("g4", "g4-review", attempt=1, builder="old builder", reviewer="the reviewer"),
        dissent_row("g4", "g4-review", attempt=2, builder="new builder", reviewer="the reviewer"),
    ]))
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #2 | new builder | the reviewer"]


def test_c08_dissent_reviewer_position_is_the_latest_rows(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.extend([
        dissent_row("g4", "g4-review", attempt=1, builder="the builder", reviewer="old reviewer"),
        dissent_row("g4", "g4-review", attempt=2, builder="the builder", reviewer="new reviewer"),
    ]))
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #2 | the builder | new reviewer"]


def test_c09_void_latest_verdict_counts_under_unresolved(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows[2].update(verdict="void"))
    assert items_of(section(run(d).stdout, "Unresolved")) == ["acceptance:c1 #1"]


def test_c09_each_subject_in_exactly_one_verdict_section(tmp_path):
    d = rich(tmp_path)
    text = run(d).stdout
    checked = count_of(section(text, "Checked"))
    verdict_total = sum(count_of(section(text, h))
                        for h in ("Passed", "Failed", "Unresolved", "Dissent", "Escalated"))
    assert checked == 8
    assert verdict_total == checked


def test_c10_subjects_ordered_by_first_appearance_not_latest_row(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.append(acceptance_row("c1", 2, "pass")))
    assert items_of(section(run(d).stdout, "Checked")) == [
        "node:g1/g1-gate #1", "node:g3/g3-review #1", "acceptance:c1 #2", "integration #1",
    ]


def test_c10_subjects_listed_in_checks_order(tmp_path):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows.insert(0, rows.pop(3)))
    assert items_of(section(run(d).stdout, "Checked"))[0] == "integration #1"


@pytest.mark.parametrize("heading, expected", [
    ("Failed", ["node:g2/g2-a #1 | first fail", "node:g2/g2-b #1 | second fail"]),
    ("Unresolved", ["acceptance:c2 #1", "acceptance:c3 #1"]),
    ("Dissent", ["node:g4/g4-a #1 | builder says g4-a is complete | reviewer says g4-a is not",
                 "node:g4/g4-b #1 | builder says g4-b is complete | reviewer says g4-b is not"]),
    ("Escalated", ["acceptance:c4 #1", "acceptance:c5 #1"]),
])
def test_c10_section_lists_subjects_in_checks_order(tmp_path, heading, expected):
    d = two_each(tmp_path)
    assert items_of(section(run(d).stdout, heading)) == expected


@pytest.mark.parametrize("heading", ["Checked", "Unresolved", "Escalated"])
def test_c11_subject_line_is_subject_and_latest_attempt(tmp_path, heading):
    d = rich(tmp_path)
    assert items_of(section(run(d).stdout, heading)) == RICH_TEXT[heading]


def test_c12_passed_line_gives_evidence_kind(tmp_path):
    d = rich(tmp_path)
    assert items_of(section(run(d).stdout, "Passed")) == RICH_TEXT["Passed"]


# failed and dissent lines (C13, C14) -------------------------------------------------

def set_g2_sections(d, sections):
    edit_checks(d, lambda rows: rows[4].update(evidence={"kind": "excerpt", "sections": sections}))


def test_c13_failed_line_carries_excerpt(tmp_path):
    d = rich(tmp_path)
    assert items_of(section(run(d).stdout, "Failed")) == RICH_TEXT["Failed"]


def test_c13_excerpt_skips_passing_sections(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [
        {"section": "checks", "verdict": "pass", "excerpt": "passing section"},
        {"section": "usage", "verdict": "fail", "excerpt": "failing section"},
    ])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | failing section"]


def test_c13_excerpt_is_the_first_failing_section(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [
        {"section": "usage", "verdict": "fail", "excerpt": "first failing"},
        {"section": "checks", "verdict": "fail", "excerpt": "second failing"},
    ])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | first failing"]


def test_c13_excerpt_ignores_sections_not_marked_fail(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [
        {"section": "checks", "verdict": "void", "excerpt": "not a failure"},
        {"section": "usage", "verdict": "fail", "excerpt": "failing section"},
    ])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | failing section"]


def test_c13_excerpt_is_cut_at_100_characters(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [{"section": "usage", "verdict": "fail", "excerpt": "x" * 100 + "TAIL"}])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | " + "x" * 100]


def test_c13_excerpt_newline_becomes_space(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [{"section": "usage", "verdict": "fail", "excerpt": "first line\nsecond line"}])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | first line second line"]


def test_c13_failed_without_fail_section_keeps_separator(tmp_path):
    d = rich(tmp_path)
    set_g2_sections(d, [])
    assert items_of(section(run(d).stdout, "Failed")) == ["node:g2/g2-gate #5 | "]


def test_c14_dissent_line_gives_both_positions(tmp_path):
    d = rich(tmp_path)
    assert items_of(section(run(d).stdout, "Dissent")) == RICH_TEXT["Dissent"]


def test_c14_first_position_is_the_section_named_by_dissent(tmp_path):
    d = rich(tmp_path)

    def dissent_names_checks(rows):
        rows[7]["evidence"]["sections"] = [
            {"section": "usage", "verdict": "pass", "excerpt": "usage text"},
            {"section": "checks", "verdict": "pass", "excerpt": "checks text"},
        ]
        rows[7]["dissent"]["section"] = "checks"
    edit_checks(d, dissent_names_checks)
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #8 | checks text | " + REVIEWER,
    ]


def test_c14_first_position_empty_when_no_section_matches(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[7]["dissent"].update(section="checks"))
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #8 |  | " + REVIEWER,
    ]


def test_c14_dissent_reviewer_text_is_not_cut(tmp_path):
    d = rich(tmp_path)

    def short_builder_long_reviewer(rows):
        rows[7]["evidence"]["sections"][0]["excerpt"] = "ok"
        rows[7]["dissent"]["reviewer_excerpt"] = "r" * 150
    edit_checks(d, short_builder_long_reviewer)
    assert items_of(section(run(d).stdout, "Dissent")) == ["node:g4/g4-review #8 | ok | " + "r" * 150]


def test_c14_dissent_first_position_is_not_cut(tmp_path):
    d = rich(tmp_path)

    def long_builder_short_reviewer(rows):
        rows[7]["evidence"]["sections"][0]["excerpt"] = "b" * 150
        rows[7]["dissent"]["reviewer_excerpt"] = "ok"
    edit_checks(d, long_builder_short_reviewer)
    assert items_of(section(run(d).stdout, "Dissent")) == ["node:g4/g4-review #8 | " + "b" * 150 + " | ok"]


def test_c14_dissent_reviewer_newline_becomes_space(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[7]["dissent"].update(
        reviewer_excerpt="reviewer line one\nreviewer line two"))
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #8 | " + BUILDER + " | reviewer line one reviewer line two",
    ]


def test_c14_dissent_first_position_newline_becomes_space(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[7]["evidence"]["sections"][0].update(
        excerpt="builder line one\nbuilder line two"))
    assert items_of(section(run(d).stdout, "Dissent")) == [
        "node:g4/g4-review #8 | builder line one builder line two | " + REVIEWER,
    ]


# unchecked rules, assumptions, audits, usage (C15 to C19) ----------------------------

def coverage_rule_lines(d):
    cov = subprocess.run([sys.executable, str(COVERAGE), str(d)], capture_output=True, text=True)
    return [line.split("\t") for line in cov.stdout.splitlines()
            if len(line.split("\t")) >= 2 and line.split("\t")[1] in ("uncovered", "unchecked")]


def test_c15_imports_coverage_and_defines_no_analyse_or_load_record():
    tree = ast.parse(REPORT.read_text(encoding="utf-8"))
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    imports_coverage = any(
        (isinstance(node, ast.Import) and any(a.name == "coverage" for a in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "coverage")
        for node in ast.walk(tree))
    assert imports_coverage
    assert not ({"analyse", "load_record"} & defined)


def test_c15_unchecked_rule_ids_match_coverage_buckets_in_order(tmp_path):
    d = rich(tmp_path)
    lines = items_of(section(run(d).stdout, "Unchecked rules"))
    got = [line.split("\t")[0] for line in lines if line.split("\t")[1:2] and line.split("\t")[1] in ("uncovered", "unchecked")]
    assert got == [parts[0] for parts in coverage_rule_lines(d)]
    assert got == ["s-gap", "s-extra"]


def test_c16_uncovered_line_is_rule_and_bucket(tmp_path):
    d = rich(tmp_path)
    assert "s-gap\tuncovered" in items_of(section(run(d).stdout, "Unchecked rules"))


def test_c16_unchecked_line_is_rule_bucket_and_reason(tmp_path):
    d = rich(tmp_path)
    assert "s-extra\tunchecked\tneeds a live endpoint" in items_of(section(run(d).stdout, "Unchecked rules"))


def test_c16_unchecked_reason_newline_becomes_space(tmp_path):
    d = rich(tmp_path)
    edit_progress(d, lambda p: p.update(unchecked_rules=[{"id": "s-extra", "reason": "needs a\nlive endpoint"}]))
    assert "s-extra\tunchecked\tneeds a live endpoint" in items_of(section(run(d).stdout, "Unchecked rules"))


def test_c16_exercised_rules_are_not_listed(tmp_path):
    d = rich(tmp_path)
    ids = [line.split("\t")[0] for line in items_of(section(run(d).stdout, "Unchecked rules"))]
    assert "s-namematch" not in ids
    assert "s-verdicts" not in ids


def test_c17_assumptions_framing_then_progress(tmp_path):
    d = make_record(tmp_path)
    assert items_of(section(run(d).stdout, "Assumptions")) == [
        "framing a1: the record format is what the spec states",
        "progress a1: yes",
    ]


def test_c17_assumptions_keep_file_order_within_each_source(tmp_path):
    d = make_record(tmp_path)
    edit_framing(d, lambda f: f["assumptions"].append({"id": "a2", "text": "second framing"}))
    edit_progress(d, lambda p: p["assumptions"].append({"id": "a2", "assumed": "no"}))
    assert items_of(section(run(d).stdout, "Assumptions")) == [
        "framing a1: the record format is what the spec states",
        "framing a2: second framing",
        "progress a1: yes",
        "progress a2: no",
    ]


def test_c17_framing_assumption_newline_becomes_space(tmp_path):
    d = make_record(tmp_path)
    edit_framing(d, lambda f: f["assumptions"][0].update(text="first line\nsecond line"))
    assert "framing a1: first line second line" in items_of(section(run(d).stdout, "Assumptions"))


def test_c17_progress_assumption_newline_becomes_space(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["assumptions"][0].update(assumed="first\nsecond"))
    assert "progress a1: first second" in items_of(section(run(d).stdout, "Assumptions"))


def test_c18_audit_notes_precede_counts(tmp_path):
    d = make_record(tmp_path)
    items = items_of(section(run(d).stdout, "Audits"))
    note_at = next(i for i, line in enumerate(items) if line.startswith("note: "))
    rows_at = next(i for i, line in enumerate(items) if line.startswith("evidence rows: "))
    assert note_at < rows_at


def test_c18_notes_keep_file_order(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes=["first note", "second note"]))
    notes = [line for line in items_of(section(run(d).stdout, "Audits")) if line.startswith("note: ")]
    assert notes == ["note: first note", "note: second note"]


def test_c18_note_newline_becomes_space(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes=["line one\nline two"]))
    assert "note: line one line two" in items_of(section(run(d).stdout, "Audits"))


@pytest.mark.parametrize("line", [
    "note: auditor noted checkrows exits 0 on d1 and d4",
    "evidence rows: 9",
    "evidence miscited: 2",
    "evidence unfound: 5",
    "evidence verdict: fail",
    "wellformed exit code: 3",
])
def test_c18_audit_line_label_and_value(tmp_path, line):
    d = audit_values(tmp_path)
    assert line in items_of(section(run(d).stdout, "Audits"))


def test_c18_count_lines_in_order(tmp_path):
    d = audit_values(tmp_path)
    labels = [line.split(":")[0] for line in items_of(section(run(d).stdout, "Audits"))]
    assert labels[1:5] == ["evidence rows", "evidence miscited", "evidence unfound", "evidence verdict"]


def test_c18_wellformed_exit_code_is_last(tmp_path):
    d = audit_values(tmp_path)
    assert items_of(section(run(d).stdout, "Audits"))[-1] == "wellformed exit code: 3"


def test_c19_usage_scalars_in_order(tmp_path):
    d = make_record(tmp_path)
    labels = [line.split(":")[0] for line in items_of(section(run(d).stdout, "Usage"))]
    assert labels == ["consumed", "limit", "unit"]


@pytest.mark.parametrize("line", ["consumed: 7", "limit: 30", "unit: node_runs"])
def test_c19_usage_scalar_label_and_value(tmp_path, line):
    d = make_record(tmp_path)
    assert line in items_of(section(run(d).stdout, "Usage"))


def test_c19_reserve_entry_lists_only_the_fields_it_has(tmp_path):
    d = rich(tmp_path)
    assert items_of(section(run(d).stdout, "Usage"))[3:] == [
        "reserve: correction_return node=g2",
        "reserve: audit audit=evidence",
    ]


def test_c19_reserve_fields_in_node_attempt_audit_order(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["usage"].update(
        reserve_runs=[{"audit": "evidence", "attempt": 2, "node": "g2", "kind": "correction_return"}]))
    assert items_of(section(run(d).stdout, "Usage"))[3:] == [
        "reserve: correction_return node=g2 attempt=2 audit=evidence"]


def test_c19_reserve_entries_keep_file_order(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["usage"].update(
        reserve_runs=[{"kind": "second_kind"}, {"kind": "first_kind"}]))
    assert items_of(section(run(d).stdout, "Usage"))[3:] == ["reserve: second_kind", "reserve: first_kind"]


# report structure (C20 to C24) ------------------------------------------------------

def test_c20_ten_sections_in_order_and_no_other_heading(tmp_path):
    d = make_record(tmp_path)
    order, _ = split_sections(run(d).stdout)
    assert order == HEADINGS


def test_c21_count_line_follows_each_heading(tmp_path):
    d = rich(tmp_path)
    lines = run(d).stdout.splitlines()
    headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
    assert len(headings) == 10
    for i in headings:
        nxt = lines[i + 1]
        assert nxt.startswith("count: ") and nxt[len("count: "):].isdigit(), nxt


def test_c22_text_counts_match_item_lines(tmp_path):
    d = rich(tmp_path)
    _, bodies = split_sections(run(d).stdout)
    for heading in TEXT_ITEM_SECTIONS:
        body = bodies[heading]
        assert count_of(body) == len(items_of(body)) > 0, heading


def test_c22_assumptions_count_is_framing_plus_progress(tmp_path):
    d = make_record(tmp_path)
    edit_framing(d, lambda f: f["assumptions"].append({"id": "a2", "text": "second framing"}))
    assert count_of(section(run(d).stdout, "Assumptions")) == 3


def test_c22_audits_count_is_note_count(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes=["one", "two", "three"]))
    assert count_of(section(run(d).stdout, "Audits")) == 3


def test_c22_usage_count_is_reserve_count(tmp_path):
    d = rich(tmp_path)
    assert count_of(section(run(d).stdout, "Usage")) == 2


def test_c23_partial_status_is_the_final_line(tmp_path):
    d = rich(tmp_path)
    assert last_line(run(d).stdout) == "status: partial"


def test_c23_blank_line_before_each_heading_after_the_first(tmp_path):
    d = rich(tmp_path)
    lines = run(d).stdout.splitlines()
    headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
    assert len(headings) == 10
    for i in headings[1:]:
        assert lines[i - 1] == "", f"no blank line before {lines[i]!r}"


def test_c23_blank_line_before_status(tmp_path):
    d = rich(tmp_path)
    lines = run(d).stdout.splitlines()
    assert lines[-2] == ""


def test_c24_output_never_says_proven(tmp_path):
    d = rich(tmp_path)
    outputs = [run(make_record(tmp_path / "ex")).stdout, run(d).stdout, run(d, "--markdown").stdout]
    for out in outputs:
        assert "proven" not in out.lower()


# status and exit codes (C25 to C31) -------------------------------------------------

def test_c25_example_status_is_complete(tmp_path):
    d = make_record(tmp_path)
    assert last_line(run(d).stdout) == "status: complete"


@pytest.mark.parametrize("graph_list", GRAPH_LISTS)
def test_c26_nonempty_graph_list_makes_status_partial(tmp_path, graph_list):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["graph"].update({graph_list: ["g9"]}))
    assert last_line(run(d).stdout) == "status: partial"


@pytest.mark.parametrize("verdict", PARTIAL_VERDICTS)
def test_c27_latest_verdict_not_pass_makes_status_partial(tmp_path, verdict):
    d = make_record(tmp_path)
    edit_checks(d, lambda rows: rows[2].update(verdict=verdict))
    assert last_line(run(d).stdout) == "status: partial"


def test_c28_wellformed_exit_code_nonzero_makes_status_partial(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["wellformed"].update(exit_code=1))
    assert last_line(run(d).stdout) == "status: partial"


@pytest.mark.parametrize("ev_verdict", ["fail", "not_run"])
def test_c28_evidence_verdict_not_pass_makes_status_partial(tmp_path, ev_verdict):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(verdict=ev_verdict))
    assert last_line(run(d).stdout) == "status: partial"


@pytest.mark.parametrize("next_action", [
    {"kind": "blocked", "issue": "o1"},
    {"kind": "node", "node": "g9"},
])
def test_c29_next_action_not_delivery_makes_status_partial(tmp_path, next_action):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p.update(next_action=next_action))
    assert last_line(run(d).stdout) == "status: partial"


def test_c30_uncovered_rule_does_not_change_status(tmp_path):
    d = make_record(tmp_path)
    edit_rules(d, lambda rules: rules.append(
        {"id": "s-gap", "spec": "graph-prompt-v2.7.md", "rule": "x", "section": "layer_5_gates",
         "quote": "x", "concerns": ["deliverable"]}))
    res = run(d)
    assert res.returncode == 0
    assert last_line(res.stdout) == "status: complete"


def test_c30_unchecked_rule_does_not_change_status(tmp_path):
    d = make_record(tmp_path)
    edit_rules(d, lambda rules: rules.append(
        {"id": "s-extra", "spec": "graph-prompt-v2.7.md", "rule": "x", "section": "layer_5_gates",
         "quote": "x", "concerns": ["deliverable"]}))
    edit_progress(d, lambda p: p.update(unchecked_rules=[{"id": "s-extra", "reason": "read by hand"}]))
    res = run(d)
    assert res.returncode == 0
    assert last_line(res.stdout) == "status: complete"


def test_c31_partial_record_exits_1_and_prints_report(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["graph"].update(running=["g2"]))
    res = run(d)
    assert res.returncode == 1
    assert "## Checked" in res.stdout.splitlines()
    assert last_line(res.stdout) == "status: partial"


def test_c31_complete_record_exits_0(tmp_path):
    d = make_record(tmp_path)
    assert run(d).returncode == 0


def subject_identity(row):
    s = row["subject"]
    if s["kind"] == "node":
        return ("node", s["node"], s["check"])
    if s["kind"] == "acceptance":
        return ("acceptance", s["item"])
    return ("integration",)


def test_c06_example_and_generated_records_count_each_subject_once(tmp_path):
    records = [EXAMPLE, rich(tmp_path)]
    for record in records:
        rows = read_yaml(record, "checks")["rows"]
        want = len({subject_identity(r) for r in rows})
        assert count_of(section(run_report(record).stdout, "Checked")) == want, record.name


# markdown (C33 to C38) -------------------------------------------------------------

def test_c33_markdown_headings_in_order(tmp_path):
    d = rich(tmp_path)
    order, _ = split_sections(run(d, "--markdown").stdout)
    assert order == HEADINGS


def test_c33_markdown_counts_equal_text_counts(tmp_path):
    d = rich(tmp_path)
    _, t_bodies = split_sections(run(d).stdout)
    _, m_bodies = split_sections(run(d, "--markdown").stdout)
    for heading in HEADINGS:
        assert count_of(m_bodies[heading]) == count_of(t_bodies[heading]), heading


def test_c33_markdown_final_status_line_equals_text(tmp_path):
    d = rich(tmp_path)
    assert last_line(run(d, "--markdown").stdout) == last_line(run(d).stdout) == "status: partial"


def test_c34_separator_row_follows_each_header_row(tmp_path):
    d = rich(tmp_path)
    _, bodies = split_sections(run(d, "--markdown").stdout)
    for heading in HEADINGS:
        header, separator = table_of(bodies[heading])[:2]
        cells = len(header.strip("|").split("|"))
        assert separator == "| " + " | ".join(["---"] * cells) + " |", heading


def test_c34_one_item_row_per_counted_item(tmp_path):
    d = rich(tmp_path)
    _, bodies = split_sections(run(d, "--markdown").stdout)
    for heading in TEXT_ITEM_SECTIONS:
        assert len(table_of(bodies[heading])[2:]) == count_of(bodies[heading]) > 0, heading


@pytest.mark.parametrize("heading", TEXT_ITEM_SECTIONS)
def test_c34_empty_section_prints_no_table(tmp_path, heading):
    d = empty_record(tmp_path)
    body = section(run(d, "--markdown").stdout, heading)
    assert count_of(body) == 0
    assert table_of(body) == []


def test_c34_usage_table_printed_when_empty(tmp_path):
    d = make_record(tmp_path)
    body = section(run(d, "--markdown").stdout, "Usage")
    assert count_of(body) == 0
    assert table_of(body)[0] == "| Item | Value |"


def test_c34_audits_table_printed_with_no_notes(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes=[]))
    body = section(run(d, "--markdown").stdout, "Audits")
    assert count_of(body) == 0
    assert table_of(body)[0] == "| Item | Value |"


@pytest.mark.parametrize("heading", ["Checked", "Passed", "Failed", "Unresolved", "Dissent", "Escalated"])
def test_c35_verdict_section_header_row(tmp_path, heading):
    d = rich(tmp_path)
    assert table_of(section(run(d, "--markdown").stdout, heading))[0] == HEADER_ROWS[heading]


@pytest.mark.parametrize("heading", ["Checked", "Passed", "Failed", "Unresolved", "Dissent", "Escalated"])
def test_c35_verdict_section_item_rows(tmp_path, heading):
    d = rich(tmp_path)
    assert table_of(section(run(d, "--markdown").stdout, heading))[2:] == RICH_MARKDOWN[heading]


@pytest.mark.parametrize("heading", ["Unchecked rules", "Assumptions"])
def test_c36_header_row(tmp_path, heading):
    d = rich(tmp_path)
    assert table_of(section(run(d, "--markdown").stdout, heading))[0] == HEADER_ROWS[heading]


def test_c36_uncovered_row_has_empty_reason_cell(tmp_path):
    d = rich(tmp_path)
    assert "| s-gap | uncovered |  |" in table_of(section(run(d, "--markdown").stdout, "Unchecked rules"))


def test_c36_unchecked_row_has_reason_cell(tmp_path):
    d = rich(tmp_path)
    assert "| s-extra | unchecked | needs a live endpoint |" in table_of(
        section(run(d, "--markdown").stdout, "Unchecked rules"))


def test_c36_framing_assumption_row_has_framing_source(tmp_path):
    d = rich(tmp_path)
    assert "| framing | a1 | the record format is what the spec states |" in table_of(
        section(run(d, "--markdown").stdout, "Assumptions"))


def test_c36_progress_assumption_row_has_progress_source(tmp_path):
    d = rich(tmp_path)
    assert "| progress | a1 | yes |" in table_of(section(run(d, "--markdown").stdout, "Assumptions"))


@pytest.mark.parametrize("heading", ["Audits", "Usage"])
def test_c37_header_row(tmp_path, heading):
    d = rich(tmp_path)
    assert table_of(section(run(d, "--markdown").stdout, heading))[0] == HEADER_ROWS[heading]


@pytest.mark.parametrize("row", [
    "| note | auditor noted checkrows exits 0 on d1 and d4 |",
    "| evidence rows | 9 |",
    "| evidence miscited | 2 |",
    "| evidence unfound | 5 |",
    "| evidence verdict | fail |",
    "| wellformed exit code | 3 |",
])
def test_c37_audits_item_value_row(tmp_path, row):
    d = audit_values(tmp_path)
    assert row in table_of(section(run(d, "--markdown").stdout, "Audits"))


@pytest.mark.parametrize("row", [
    "| consumed | 7 |",
    "| limit | 30 |",
    "| unit | node_runs |",
    "| reserve | correction_return node=g2 |",
    "| reserve | audit audit=evidence |",
])
def test_c37_usage_item_value_row(tmp_path, row):
    d = rich(tmp_path)
    assert row in table_of(section(run(d, "--markdown").stdout, "Usage"))


def test_c38_markdown_cell_escapes_pipe(tmp_path):
    d = rich(tmp_path)
    edit_checks(d, lambda rows: rows[4].update(
        evidence={"kind": "excerpt", "sections": [
            {"section": "usage", "verdict": "fail", "excerpt": "usage | missing section"}]}))
    edit_progress(d, lambda p: p.update(unchecked_rules=[{"id": "s-extra", "reason": "needs a | live endpoint"}]))
    md_lines = run(d, "--markdown").stdout.splitlines()
    assert "| node:g2/g2-gate | 5 | usage \\| missing section |" in md_lines
    assert "| s-extra | unchecked | needs a \\| live endpoint |" in md_lines


def test_c38_markdown_cell_newline_becomes_space(tmp_path):
    d = make_record(tmp_path)
    edit_progress(d, lambda p: p["audits"]["evidence"].update(notes=["line one\nline two"]))
    md_lines = run(d, "--markdown").stdout.splitlines()
    assert "| note | line one line two |" in md_lines


# read-only, dependencies and files (C39 to C41) -------------------------------------

def snapshot(d):
    """Bytes and modification time of every file, and the presence of every directory."""
    out = {}
    for p in d.rglob("*"):
        rel = str(p.relative_to(d))
        if p.is_file():
            out[rel] = (p.read_bytes(), p.stat().st_mtime_ns)
        else:
            out[rel] = None
    return out


def test_c39_writes_nothing_under_run_dir(tmp_path):
    d = rich(tmp_path)
    before = snapshot(d)
    run(d)
    run(d, "--markdown")
    assert snapshot(d) == before


def test_c40_imports_are_stdlib_yaml_and_coverage_only():
    tree = ast.parse(REPORT.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules.add((node.module or "").split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"yaml", "coverage"}
    assert modules <= allowed, f"non-allowed imports: {sorted(modules - allowed)}"


@pytest.mark.parametrize("name", ["report.py", "test_report.py", "REPORT-SPEC.md", "coverage.py", "validate.py"])
def test_c41_deliverable_file_sits_in_graph_record(name):
    assert (HERE / name).is_file()


def test_c41_spec_names_report_beside_coverage_and_validate():
    clause = next(line for line in (HERE / "REPORT-SPEC.md").read_text(encoding="utf-8").splitlines()
                  if line.startswith("C41."))
    for name in ("validate.py", "coverage.py", "report.py", "test_report.py", "REPORT-SPEC.md"):
        assert name in clause
        assert (HERE / name).is_file()
