"""X34-X37 (v3.6, D67-D70): worktree isolation as the record states it. Run: python -m pytest -q test_workspace_rules.py"""
import copy

import pytest

from test_v2_rules import load, run

B0, G1, G1B, G3B, G3, IN = ("0" * 39 + d for d in "123456")
SLUG = "2026-11-20-demo"


def worktree_record():
    r = load()
    rows = r["checks"]["rows"]
    rows[0]["workspace"] = {"branch": f"graph/{SLUG}/g1/a1", "base": B0, "commit": G1, "changed": ["code/checkrows.py"]}
    rows[1]["workspace"] = {"branch": f"graph/{SLUG}/g3/a1", "base": G3B, "commit": G3, "changed": ["README.md"]}
    integ = {"branch": f"graph/{SLUG}/integration/a1", "base": B0, "commit": IN, "changed": ["README.md", "code/checkrows.py"]}
    rows[2]["workspace"] = copy.deepcopy(integ)
    rows[3]["workspace"] = copy.deepcopy(integ)
    r["progress"]["workspace"] = {"kind": "worktree", "repo": "/work/repo", "base": B0, "person_branch": "main",
                                  "root": "/work/repo/.git/graph-worktrees/" + SLUG,
                                  "integration_branch": integ["branch"], "landed": {"kind": "fast_forward", "commit": IN}}
    return r


def rules(rec, tmp_path):
    code, out = run(rec, tmp_path)
    return code, {line.split(" ", 1)[0] for line in out.splitlines()}, out


def test_worktree_record_holds(tmp_path):
    code, _, out = rules(worktree_record(), tmp_path)
    assert code == 0, out


def test_directory_record_holds(tmp_path):
    r = load(); r["progress"]["workspace"] = {"kind": "directory", "reason": "the deliverable is not in a git repository"}
    assert rules(r, tmp_path)[0] == 0


def test_directory_requires_reason_and_forbids_git_fields(tmp_path):
    r = load(); r["progress"]["workspace"] = {"kind": "directory", "base": B0}
    code, found, _ = rules(r, tmp_path)
    assert code == 1 and "SCHEMA" in found


def test_commit_must_be_a_full_object_id(tmp_path):
    r = worktree_record(); r["checks"]["rows"][0]["workspace"]["commit"] = "abc123"
    assert "SCHEMA" in rules(r, tmp_path)[1]


@pytest.mark.parametrize("mutate", ["drop_row_workspace", "workspace_without_worktree"])
def test_x34_presence(tmp_path, mutate):
    r = worktree_record()
    if mutate == "drop_row_workspace":
        del r["checks"]["rows"][1]["workspace"]
    else:
        r["progress"]["workspace"] = {"kind": "directory", "reason": "no git"}
    code, found, _ = rules(r, tmp_path)
    assert code == 1 and "X34" in found


def test_x34_not_run_rows_need_no_workspace(tmp_path):
    r = worktree_record()
    row = r["checks"]["rows"][1]
    del row["workspace"]
    row.update(verdict="unresolved", evidence={"kind": "not_run", "reason": "not dispatched yet"})
    r["progress"]["graph"]["accepted"].remove("g3"); r["progress"]["graph"]["not_started"].append("g3")
    r["progress"]["next_action"] = {"kind": "node", "node": "g3"}
    assert "X34" not in rules(r, tmp_path)[1]


def test_x35_shared_branch_and_split_integration(tmp_path):
    r = worktree_record(); r["checks"]["rows"][1]["workspace"]["branch"] = f"graph/{SLUG}/g1/a1"
    assert "X35" in rules(r, tmp_path)[1]
    r = worktree_record(); r["checks"]["rows"][3]["workspace"]["commit"] = G1B
    assert "X35" in rules(r, tmp_path)[1]


def retry(r, cause):
    rows = r["checks"]["rows"]
    second = copy.deepcopy(rows[0])
    rows[0]["verdict"] = "fail"; rows[0]["evidence"]["actual_exit"] = 1
    second["attempt"] = 2
    second["workspace"] = {"branch": f"graph/{SLUG}/g1/a2", "base": G1B, "commit": G1B.replace("2", "7"), "changed": ["code/checkrows.py"]}
    rows.insert(1, second)
    r["progress"]["hypotheses"] = [{"node": "g1", "before_attempt": 2, "cause": cause, "disconfirmation": "the retry passes"}]
    return r


def test_x35_retry_must_start_from_previous_attempt(tmp_path):
    assert "X35" in rules(retry(worktree_record(), "builder_error"), tmp_path)[1]
    r = retry(worktree_record(), "builder_error"); r["checks"]["rows"][1]["workspace"]["base"] = G1
    assert "X35" not in rules(r, tmp_path)[1]


def test_x35_rebuilt_base_after_upstream_reopened(tmp_path):
    assert "X35" not in rules(retry(worktree_record(), "upstream_field"), tmp_path)[1]


def test_x36_write_outside_scope(tmp_path):
    r = worktree_record(); r["checks"]["rows"][1]["workspace"]["changed"].append("code/checkrows.py")
    code, found, out = rules(r, tmp_path)
    assert code == 1 and "X36" in found and "code/checkrows.py is outside writes" in out


def test_x36_directory_writes_entry(tmp_path):
    r = worktree_record()
    g1 = r["graph"]["nodes"][0]; g1["writes"] = ["code/"]
    r["checks"]["rows"][0]["workspace"]["changed"] = ["code/checkrows.py", "code/helpers.py"]
    assert "X36" not in rules(r, tmp_path)[1]


def test_x36_ignores_failed_attempts(tmp_path):
    r = retry(worktree_record(), "builder_error")
    r["checks"]["rows"][1]["workspace"]["base"] = G1
    r["checks"]["rows"][0]["workspace"]["changed"].append("README.md")
    assert "X36" not in rules(r, tmp_path)[1]


def test_x37_integration_branch_and_landing(tmp_path):
    r = worktree_record(); r["progress"]["workspace"]["integration_branch"] = f"graph/{SLUG}/integration/a0"
    assert "X37" in rules(r, tmp_path)[1]
    r = worktree_record(); del r["progress"]["workspace"]["landed"]
    assert "X37" in rules(r, tmp_path)[1]
    r = worktree_record(); r["progress"]["workspace"]["landed"]["commit"] = G3
    assert "X37" in rules(r, tmp_path)[1]
    r = worktree_record(); r["progress"]["workspace"]["landed"] = {"kind": "not_landed", "reason": "main moved since the run base"}
    assert rules(r, tmp_path)[0] == 0
