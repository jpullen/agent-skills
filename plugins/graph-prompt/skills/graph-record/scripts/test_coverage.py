"""Tests for coverage.py, the rule-coverage reporter, to the contract COVERAGE-SPEC.md.

Run: python -m pytest -q test_coverage.py

Each test is named for the contract clause(s) it exercises and checks one behaviour.
Fixtures are copies of example/ made in tmp_path and mutated there. coverage.py is run as a
subprocess so that exit codes and stderr are observable.
"""
import ast
import pathlib
import re
import shutil
import subprocess
import sys

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
EXAMPLE = HERE / "example"
COVERAGE = HERE / "coverage.py"
VALIDATE = HERE / "validate.py"
BUCKETS = ("exercised", "unchecked", "uncovered")
X32_UNCOVERED = "X32 rules {}: concerns the deliverable but no checks row exercises it and progress.unchecked_rules does not list it"


# helpers ----------------------------------------------------------------------

def make_record(tmp_path):
    d = tmp_path / "rec"
    shutil.copytree(EXAMPLE, d)
    return d


def read_yaml(d, name):
    return yaml.safe_load((d / f"{name}.yaml").read_text(encoding="utf-8"))


def write_yaml(d, name, data):
    (d / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def add_rule(d, rule_id, concerns=("deliverable",)):
    data = read_yaml(d, "rules")
    data["rules"].append({"id": rule_id, "spec": "graph-prompt-v2.7.md", "concerns": list(concerns)})
    write_yaml(d, "rules", data)


def set_unchecked(d, entries):
    prog = read_yaml(d, "progress")
    prog["unchecked_rules"] = entries
    write_yaml(d, "progress", prog)


def edit_row(d, index, **fields):
    data = read_yaml(d, "checks")
    data["rows"][index].update(fields)
    write_yaml(d, "checks", data)


def insert_row(d, index, row):
    data = read_yaml(d, "checks")
    data["rows"].insert(index, row)
    write_yaml(d, "checks", data)


def run_argv(*argv):
    return subprocess.run([sys.executable, str(COVERAGE), *map(str, argv)], capture_output=True, text=True)


def run(d, *extra):
    return run_argv(d, *extra)


def rule_lines(stdout):
    out = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1] in BUCKETS:
            out.append(line)
    return out


def rule_line(stdout, rule_id):
    found = [line for line in rule_lines(stdout) if line.split("\t")[0] == rule_id]
    assert len(found) == 1, f"expected exactly one rule line for {rule_id}, found {found}"
    return found[0]


def summary_line(stdout):
    found = [line for line in stdout.splitlines() if line.startswith("summary:")]
    assert len(found) == 1, f"expected one summary line, found {found}"
    return found[0]


def table_rows(stdout):
    rows = []
    for line in stdout.splitlines():
        if line.startswith("| "):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def assert_parse_error(res):
    assert res.returncode == 2
    assert res.stdout == ""
    assert res.stderr.startswith("usage:")


# usage and parse errors (C2, C4) ------------------------------------------------

def test_c2_no_argument_is_usage_error():
    res = run_argv()
    assert res.returncode == 2
    assert res.stderr.startswith("usage:")
    assert res.stdout == ""


def test_c2_two_run_dirs_is_usage_error(tmp_path):
    d = make_record(tmp_path)
    res = run_argv(d, d)
    assert_parse_error(res)


def test_c2_c29_unknown_option_exit_2_empty_stdout(tmp_path):
    d = make_record(tmp_path)
    res = run(d, "--bogus")
    assert_parse_error(res)


def test_c2_run_dir_not_a_directory_is_usage_error(tmp_path):
    res = run_argv(tmp_path / "no-such-run")
    assert_parse_error(res)


def test_c4_missing_record_file_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "checks.yaml").unlink()
    res = run(d)
    assert_parse_error(res)
    assert "checks.yaml" in res.stderr


def test_c4_yaml_syntax_error_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "rules.yaml").write_text("rules: [unclosed\n", encoding="utf-8")
    res = run(d)
    assert_parse_error(res)


def test_c4_duplicate_key_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "progress.yaml").write_text("enforcement: {kind: a}\nenforcement: {kind: b}\n", encoding="utf-8")
    res = run(d)
    assert_parse_error(res)
    assert "duplicate" in res.stderr


def test_c4_rules_shape_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    write_yaml(d, "rules", {"rules": "not a list"})
    assert_parse_error(run(d))


def test_c4_checks_shape_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    write_yaml(d, "checks", {"rows": "not a list"})
    assert_parse_error(run(d))


def test_c4_progress_not_mapping_is_parse_error(tmp_path):
    d = make_record(tmp_path)
    (d / "progress.yaml").write_text("- just\n- a list\n", encoding="utf-8")
    assert_parse_error(run(d))


def test_c3_other_record_files_not_read(tmp_path):
    d = make_record(tmp_path)
    for name in ("graph.yaml", "framing.yaml", "lessons.yaml"):
        (d / name).unlink()
    res = run(d)
    assert res.returncode == 0
    assert summary_line(res.stdout).startswith("summary:")


# which rules are reported (C6, C7, C8, C22, C23) ---------------------------------

def test_c7_rule_lines_follow_rules_yaml_order(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-zeta")
    add_rule(d, "s-alpha")
    res = run(d)
    ids = [line.split("\t")[0] for line in rule_lines(res.stdout)]
    assert ids == ["s-namematch", "s-verdicts", "s-zeta", "s-alpha"]


def test_c8_non_deliverable_rule_has_no_rule_line(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-manual", concerns=("graph",))
    res = run(d)
    assert "s-manual" not in [line.split("\t")[0] for line in rule_lines(res.stdout)]


def test_c23_manual_section_lists_non_deliverable_rule(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-manual", concerns=("graph",))
    lines = run(d).stdout.splitlines()
    assert "manual (not counted in the summary):" in lines
    assert "  s-manual graph" in lines


def test_c23_manual_section_omitted_when_empty(tmp_path):
    d = make_record(tmp_path)
    assert "manual (not counted in the summary):" not in run(d).stdout


def test_c22_summary_counts_each_bucket(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-unchecked-one")
    add_rule(d, "s-gap")
    add_rule(d, "s-manual", concerns=("graph",))
    set_unchecked(d, [{"id": "s-unchecked-one", "reason": "needs a live endpoint"}])
    res = run(d)
    assert summary_line(res.stdout) == "summary: exercised=2 unchecked=1 uncovered=1"


# bucket and detail field (C10, C11, C12, C19, C20) -----------------------------------

def test_c12_unlisted_deliverable_rule_is_uncovered(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    assert rule_line(run(d).stdout, "s-gap").split("\t")[1] == "uncovered"


def test_c20_uncovered_line_has_no_detail_field(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    assert rule_line(run(d).stdout, "s-gap") == "s-gap\tuncovered"


def test_c10_failing_acceptance_row_still_exercises(tmp_path):
    d = make_record(tmp_path)
    edit_row(d, 2, verdict="fail")
    assert rule_line(run(d).stdout, "s-namematch").split("\t")[1] == "exercised"


def test_c20_exercised_detail_names_item_attempt_verdict(tmp_path):
    d = make_record(tmp_path)
    assert rule_line(run(d).stdout, "s-namematch") == "s-namematch\texercised\tc1#1=pass"


def test_c20_exercised_detail_uses_newest_attempt(tmp_path):
    d = make_record(tmp_path)
    insert_row(d, 4, {
        "subject": {"kind": "acceptance", "item": "c1"}, "attempt": 2, "requirement": "both scripts exit 0 on clean",
        "type": "exec", "verdict": "fail", "exercises": [],
    })
    assert rule_line(run(d).stdout, "s-namematch") == "s-namematch\texercised\tc1#2=fail"


def test_c20_exercised_items_in_checks_order(tmp_path):
    d = make_record(tmp_path)
    insert_row(d, 2, {
        "subject": {"kind": "acceptance", "item": "c2"}, "attempt": 1, "requirement": "second item",
        "type": "exec", "verdict": "pass", "exercises": ["s-namematch"],
    })
    assert rule_line(run(d).stdout, "s-namematch") == "s-namematch\texercised\tc2#1=pass,c1#1=pass"


def test_c20_unchecked_detail_is_reason(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-extra")
    set_unchecked(d, [{"id": "s-extra", "reason": "needs a live endpoint"}])
    assert rule_line(run(d).stdout, "s-extra") == "s-extra\tunchecked\tneeds a live endpoint"


def test_c20_c21_reason_newlines_keep_line_whole(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-extra")
    set_unchecked(d, [{"id": "s-extra", "reason": "needs a live\nendpoint"}])
    assert rule_line(run(d).stdout, "s-extra") == "s-extra\tunchecked\tneeds a live endpoint"


def test_c9_c17_c31_node_row_exercises_ignored(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-only-node")
    edit_row(d, 0, exercises=["s-only-node"])
    assert rule_line(run(d).stdout, "s-only-node") == "s-only-node\tuncovered"


# findings and exit codes (C13, C14, C16, C27, C28) ------------------------------------

def test_c13_unchecked_id_not_a_rule(tmp_path):
    d = make_record(tmp_path)
    set_unchecked(d, [{"id": "s-ghost", "reason": "no such rule"}])
    res = run(d)
    assert "X32 progress.unchecked_rules: s-ghost is not a rules id" in res.stdout.splitlines()
    assert res.returncode == 1


def test_c14_exercised_and_unchecked_is_finding(tmp_path):
    d = make_record(tmp_path)
    set_unchecked(d, [{"id": "s-namematch", "reason": "no check"}])
    res = run(d)
    assert "X32 progress.unchecked_rules: s-namematch is both exercised and listed as unchecked" in res.stdout.splitlines()
    assert res.returncode == 1


def test_c14_exercised_bucket_wins_over_unchecked(tmp_path):
    d = make_record(tmp_path)
    set_unchecked(d, [{"id": "s-namematch", "reason": "no check"}])
    assert rule_line(run(d).stdout, "s-namematch").split("\t")[1] == "exercised"


def test_c28_uncovered_rule_exits_1_with_x32_finding(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    res = run(d)
    assert res.returncode == 1
    assert X32_UNCOVERED.format("s-gap") in res.stdout.splitlines()


def test_c16_x09_finding_for_unknown_exercise_id(tmp_path):
    d = make_record(tmp_path)
    edit_row(d, 2, exercises=["s-namematch", "s-verdicts", "s-nope"])
    assert "X09 c1#1: exercises s-nope not in rules" in run(d).stdout.splitlines()


def test_c16_x09_does_not_change_exit_code(tmp_path):
    d = make_record(tmp_path)
    edit_row(d, 2, exercises=["s-namematch", "s-verdicts", "s-nope"])
    assert run(d).returncode == 0


def test_c27_exit_0_when_x32_holds(tmp_path):
    d = make_record(tmp_path)
    assert run(d).returncode == 0


# markdown (C24, C25) -------------------------------------------------------------

def test_c24_markdown_table_rows(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    res = run(d, "--markdown")
    rows = table_rows(res.stdout)
    assert rows[0] == ["Rule", "Bucket", "Detail"]
    by_rule = {row[0]: row for row in rows[1:]}
    assert by_rule["s-namematch"] == ["s-namematch", "exercised", "c1#1=pass"]
    assert by_rule["s-gap"] == ["s-gap", "uncovered", ""]


def test_c25_markdown_keeps_summary_line(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    res = run(d, "--markdown")
    assert summary_line(res.stdout) == "summary: exercised=2 unchecked=0 uncovered=1"


# read-only and imports (C30, C33) ------------------------------------------------

def test_c1_command_line_with_and_without_markdown(tmp_path):
    d = make_record(tmp_path)
    plain = run(d)
    markdown = run(d, "--markdown")
    assert rule_lines(plain.stdout), "without --markdown the text report prints rule lines"
    assert ["Rule", "Bucket", "Detail"] in table_rows(markdown.stdout), "--markdown prints the table header"
    assert ["Rule", "Bucket", "Detail"] not in table_rows(plain.stdout), "without --markdown no table header is printed"


def test_c5_no_schema_validation_of_rule_entries(tmp_path):
    d = make_record(tmp_path)
    data = read_yaml(d, "rules")
    data["rules"].append({"id": "s-bare", "concerns": ["deliverable"]})
    write_yaml(d, "rules", data)
    assert rule_line(run(d).stdout, "s-bare") == "s-bare\tuncovered"


def test_c6_rule_without_concerns_not_deliverable(tmp_path):
    d = make_record(tmp_path)
    data = read_yaml(d, "rules")
    data["rules"].append({"id": "s-noconcern", "spec": "graph-prompt-v2.7.md"})
    write_yaml(d, "rules", data)
    assert "s-noconcern" not in [line.split("\t")[0] for line in rule_lines(run(d).stdout)]


def test_c11_c15_listed_rule_read_as_unchecked(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-extra")
    set_unchecked(d, [{"id": "s-extra", "reason": "needs a live endpoint"}])
    assert rule_line(run(d).stdout, "s-extra").split("\t")[1] == "unchecked"


def test_c18_text_report_order_rules_summary_findings(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    out = run(d).stdout
    lines = out.splitlines()
    last_rule = max(i for i, line in enumerate(lines) if line in rule_lines(out))
    summary = next(i for i, line in enumerate(lines) if line.startswith("summary:"))
    finding = next(i for i, line in enumerate(lines) if line.startswith("X32 rules s-gap"))
    assert last_rule < summary < finding


def test_c19_rule_line_is_id_tab_bucket(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    shape = re.compile(r"[^\t]+\t(exercised|unchecked|uncovered)(\t.*)?")
    lines = rule_lines(run(d).stdout)
    assert len(lines) == 3
    assert all(shape.fullmatch(line) for line in lines)


def test_c26_all_findings_printed(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    set_unchecked(d, [{"id": "s-ghost", "reason": "x"}])
    edit_row(d, 2, exercises=["s-namematch", "s-verdicts", "s-nope"])
    out = run(d).stdout.splitlines()
    assert X32_UNCOVERED.format("s-gap") in out
    assert "X32 progress.unchecked_rules: s-ghost is not a rules id" in out
    assert "X09 c1#1: exercises s-nope not in rules" in out


def test_c34_deliverable_files_beside_validate():
    for name in ("coverage.py", "test_coverage.py", "COVERAGE-SPEC.md"):
        assert (HERE / name).is_file()
    assert VALIDATE.is_file()


def snapshot(d):
    return {str(p.relative_to(d)): (p.read_bytes() if p.is_file() else None) for p in d.rglob("*")}


def test_c30_reporter_writes_nothing_under_run_dir(tmp_path):
    d = make_record(tmp_path)
    add_rule(d, "s-gap")
    before = snapshot(d)
    run(d)
    run(d, "--markdown")
    assert snapshot(d) == before


def test_c33_imports_stdlib_and_yaml_only():
    tree = ast.parse(COVERAGE.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add("<relative>" if node.level else (node.module or "").split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"yaml"}
    assert modules <= allowed, f"non-allowed imports: {sorted(modules - allowed)}"


# agreement with validate.py on example and on records generated in tmp_path (C32) --------------------

def validate_uncovered(run_dir):
    res = subprocess.run([sys.executable, str(VALIDATE), str(run_dir), "--models", "haiku,sonnet,opus", "--all"],
                         capture_output=True, text=True)
    lines = res.stdout.splitlines()
    assert not any(line.startswith("NOTE") for line in lines), "validate.py did not evaluate the cross-file rules"
    return {m.group(1) for line in lines for m in [re.match(r"X32 rules (\S+): ", line)] if m}


def add_full_rule(d, rule_id):
    """A rules row carrying every field the schema requires, so validate.py evaluates the cross-file rules."""
    data = read_yaml(d, "rules")
    data["rules"].append({"id": rule_id, "spec": "graph-prompt-v2.7.md", "rule": f"rule {rule_id} holds",
                          "section": "layer_5_gates", "quote": f"{rule_id} holds", "concerns": ["deliverable"]})
    write_yaml(d, "rules", data)


def uncovered_variant(tmp_path):
    d = make_record(tmp_path)
    add_full_rule(d, "s-new-uncovered")
    return d


def unchecked_variant(tmp_path):
    d = make_record(tmp_path)
    add_full_rule(d, "s-new-unchecked")
    set_unchecked(d, [{"id": "s-new-unchecked", "reason": "needs a live endpoint"}])
    return d


def exercised_variant(tmp_path):
    d = make_record(tmp_path)
    add_full_rule(d, "s-new-exercised")
    data = read_yaml(d, "checks")
    row = next(r for r in data["rows"] if r["subject"]["kind"] == "acceptance")
    row["exercises"].append("s-new-exercised")
    write_yaml(d, "checks", data)
    return d


AGREEMENT_VARIANTS = {
    "example": make_record,
    "uncovered-rule": uncovered_variant,
    "unchecked-rule-with-reason": unchecked_variant,
    "acceptance-row-exercises-rule": exercised_variant,
}


@pytest.mark.parametrize("build", list(AGREEMENT_VARIANTS.values()), ids=list(AGREEMENT_VARIANTS))
def test_c32_uncovered_set_agrees_with_validate_x32(build, tmp_path):
    run_dir = build(tmp_path)
    res = run_argv(run_dir)
    assert res.returncode in (0, 1), res.stderr
    got = {line.split("\t")[0] for line in rule_lines(res.stdout) if line.split("\t")[1] == "uncovered"}
    want = validate_uncovered(run_dir)
    assert got == want, f"only in reporter: {sorted(got - want)}; only in validate.py: {sorted(want - got)}"
    buckets = {line.split("\t")[0]: line.split("\t")[1] for line in rule_lines(res.stdout)}
    expected = {uncovered_variant: ("s-new-uncovered", "uncovered"),
                unchecked_variant: ("s-new-unchecked", "unchecked"),
                exercised_variant: ("s-new-exercised", "exercised")}
    if build in expected:
        rule_id, bucket = expected[build]
        assert buckets[rule_id] == bucket
