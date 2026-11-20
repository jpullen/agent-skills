"""Tests for worktrees.py against throwaway git repositories. Run: python3 -m pytest -q (needs git, pytest, pyyaml)."""
import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / "worktrees.py"
SLUG = "2026-11-20-demo"


def sh(cwd, *args):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def wt(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


GRAPH = {"nodes": [
    {"id": "b", "reads": {"sources": False, "upstream": []}, "writes": ["b.txt"]},
    {"id": "a", "reads": {"sources": False, "upstream": []}, "writes": ["a.txt", "docs/"]},
    {"id": "c", "reads": {"sources": False, "upstream": [{"node": "a", "sections": ["x"]}, {"node": "b", "sections": ["y"]}]}, "writes": ["c.txt"]},
]}


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    sh(r, "git", "init", "-q", "-b", "main")
    sh(r, "git", "config", "user.name", "Test")
    sh(r, "git", "config", "user.email", "test@example.invalid")
    for n in ("a.txt", "b.txt", "c.txt"):
        (r / n).write_text(f"{n} v0\n")
    sh(r, "git", "add", "-A"); sh(r, "git", "commit", "-q", "-m", "init")
    run_dir = r / ".graph" / SLUG
    run_dir.mkdir(parents=True)
    (run_dir / "graph.yaml").write_text(yaml.safe_dump(GRAPH))
    return r


def start(repo):
    code, s = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG, "--scope", "a.txt", "b.txt", "c.txt", "docs")
    assert code == 0, s
    return s


def build(repo, s, node, attempt, frm, files, upstream=()):
    code, n = wt("node", repo, "--slug", SLUG, "--node", node, "--attempt", attempt, "--from", frm,
                 "--graph", repo / ".graph" / SLUG / "graph.yaml", *(["--upstream", *upstream] if upstream else []))
    assert code == 0, n
    for name, text in files.items():
        p = pathlib.Path(n["worktree"]) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    code, c = wt("commit", n["worktree"], "--message", f"{node} a{attempt}")
    assert code == 0, c
    return n, c["commit"]


def test_start_records_base_and_hides_run_dir(repo):
    s = start(repo)
    assert s["base"] == sh(repo, "git", "rev-parse", "HEAD") and s["person_branch"] == "main"
    assert not str(s["root"]).startswith(str(repo / ".graph"))
    assert not (pathlib.Path(s["baseline"]) / ".graph").exists()
    assert sh(repo, "git", "status", "--porcelain") == ""


def test_start_refuses_dirty_scope_tracked_run_dir_and_existing_root(repo):
    (repo / "a.txt").write_text("dirty\n")
    code, s = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG, "--scope", "a.txt")
    assert code == 3 and s["paths"] == [" M a.txt"]
    sh(repo, "git", "checkout", "--", "a.txt")
    start(repo)
    code, s = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG)
    assert code == 3 and "already exists" in s["error"]


def test_start_refuses_tracked_run_dir(repo):
    sh(repo, "git", "add", "-f", ".graph"); sh(repo, "git", "commit", "-q", "-m", "track record")
    code, s = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG)
    assert code == 3 and "tracked" in s["error"]


def test_parallel_nodes_are_isolated_and_scope_is_checked(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n", "docs/x.md": "x\n"})
    nb, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    assert (pathlib.Path(nb["worktree"]) / "a.txt").read_text() == "a.txt v0\n"
    code, sc = wt("scope", na["worktree"], "--base", na["base"], "--commit", ca, "--graph", repo / ".graph" / SLUG / "graph.yaml", "--node", "a")
    assert code == 0 and sorted(sc["changed"]) == ["a.txt", "docs/x.md"] and sc["outside"] == []
    _, bad = build(repo, s, "b", 2, cb, {"a.txt": "escaped\n"})
    code, sc = wt("scope", nb["worktree"], "--base", cb, "--commit", bad, "--writes", "b.txt")
    assert code == 1 and sc["outside"] == ["a.txt"]
    assert (repo / "a.txt").read_text() == "a.txt v0\n"  # the main checkout is untouched


def test_fan_in_base_merges_upstreams_in_topological_order(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    nc, cc = build(repo, s, "c", 1, s["base"], {"c.txt": "c v1\n"}, upstream=[f"b={cb}", f"a={ca}"])
    log = sh(repo, "git", "log", "--first-parent", "--format=%s", "--reverse", f"{s['base']}..{nc['base']}").splitlines()
    assert log == ["a a1", f"graph({SLUG}): c a1 base <- b"]  # a fast-forwards first (topological, ties by id), then b merges
    assert sh(repo, "git", "rev-parse", nc["base"] + "^2") == cb
    tree = pathlib.Path(nc["worktree"])
    assert (tree / "a.txt").read_text() == "a v1\n" and (tree / "b.txt").read_text() == "b v1\n"


def test_conflict_is_aborted_and_reported(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"a.txt": "b wrote a\n"})  # a write outside b's writes
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"],
                 "--graph", repo / ".graph" / SLUG / "graph.yaml", "--upstream", f"a={ca}", f"b={cb}")
    assert code == 3 and r["conflicts"] == ["a.txt"] and r["merging"] == "b"
    assert sh(os.path.join(s["root"], "c"), "git", "status", "--porcelain") == ""


def test_retry_stacks_on_previous_attempt(repo):
    s = start(repo)
    _, c1 = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    n2, c2 = build(repo, s, "a", 2, c1, {"a.txt": "a v2\n"})
    assert n2["base"] == c1 and n2["branch"] == f"graph/{SLUG}/a/a2"
    assert sh(repo, "git", "diff", "--name-only", c1, c2) == "a.txt"
    code, r = wt("commit", n2["worktree"], "--message", "empty")
    assert code == 4


def record(repo, s, rows, integ=None, landed=None):
    d = repo / ".graph" / SLUG
    (d / "checks.yaml").write_text(yaml.safe_dump({"rows": rows}))
    ws = {"kind": "worktree", "repo": str(repo), "base": s["base"], "person_branch": "main", "root": s["root"],
          "integration_branch": integ or "none"}
    if landed:
        ws["landed"] = landed
    (d / "progress.yaml").write_text(yaml.safe_dump({"workspace": ws, "graph": {"accepted": ["a", "b", "c"], "dissent": []}}))  # unwrapped, as real records are (RF-63)
    return d


def row(kind, who, attempt, w, verdict="pass"):
    subj = {"kind": kind, **({"node": who, "check": f"{who}-gate"} if kind == "node" else {"item": who} if kind == "acceptance" else {})}
    return {"subject": subj, "attempt": attempt, "verdict": verdict, "workspace": w}


def test_integrate_verify_land_cleanup(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    nb, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    nc, cc = build(repo, s, "c", 1, s["base"], {"c.txt": "c v1\n"}, upstream=[f"a={ca}", f"b={cb}"])
    code, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"],
                  "--graph", repo / ".graph" / SLUG / "graph.yaml", "--accepted", f"c={cc}", f"b={cb}", f"a={ca}")
    assert code == 0 and ig["order"] == ["a", "b", "c"] and sorted(ig["changed"]) == ["a.txt", "b.txt", "c.txt"]
    ws = lambda n, c: {"branch": n["branch"], "base": n["base"], "commit": c,
                       "changed": sh(repo, "git", "diff", "--name-only", n["base"], c).splitlines()}
    rows = [row("node", "a", 1, ws(na, ca)), row("node", "b", 1, ws(nb, cb)), row("node", "c", 1, ws(nc, cc)),
            row("acceptance", "k1", 1, {"branch": ig["branch"], "base": ig["base"], "commit": ig["commit"], "changed": ig["changed"]})]
    d = record(repo, s, rows, ig["branch"])
    code, v = wt("verify", d)
    assert code == 0, v
    rows[0]["workspace"]["changed"] = ["a.txt", "b.txt"]
    record(repo, s, rows, ig["branch"])
    code, v = wt("verify", d)
    assert code == 1 and v["findings"][0].startswith("W04 a#1")
    code, ld = wt("land", repo, "--commit", ig["commit"], "--branch", "main")
    assert code == 0 and ld == {"kind": "fast_forward", "commit": ig["commit"]}
    assert (repo / "c.txt").read_text() == "c v1\n"
    rows[0]["workspace"]["changed"] = ["a.txt"]
    record(repo, s, rows, ig["branch"], ld)
    assert wt("verify", d)[0] == 0
    (pathlib.Path(nb["worktree"]) / "scratch").write_text("x")
    code, cl = wt("cleanup", repo, "--root", s["root"])
    assert code == 1 and cl["kept"] == [nb["worktree"]] and len(cl["removed"]) == 4
    assert sh(repo, "git", "branch", "--list", f"graph/{SLUG}/*").count("graph/") == 4  # branches are kept


def test_verify_finds_unconverged_integration(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    code, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"a={ca}")
    na2, ca2 = build(repo, s, "a", 2, ca, {"a.txt": "a v2\n"})  # a correction after integration
    ws = lambda n, c: {"branch": n["branch"], "base": n["base"], "commit": c, "changed": ["a.txt"]}
    rows = [row("node", "a", 1, ws(na, ca), "fail"), row("node", "a", 2, ws(na2, ca2)),
            row("integration", None, 1, {"branch": ig["branch"], "base": s["base"], "commit": ig["commit"], "changed": ["a.txt"]})]
    d = record(repo, s, rows, ig["branch"])
    code, v = wt("verify", d)
    assert code == 1 and any(x.startswith("W05 a") for x in v["findings"])


def test_land_refuses_non_fast_forward(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    (repo / "b.txt").write_text("person moved on\n")
    sh(repo, "git", "commit", "-qam", "person")
    code, ld = wt("land", repo, "--commit", ca, "--branch", "main")
    assert code == 5 and ld["kind"] == "not_landed"
    assert (repo / "a.txt").read_text() == "a.txt v0\n"


# T-47 / T-48 (run 13): every documented exit code and verify finding is reached -----

def test_usage_and_git_errors_exit_2(tmp_path, repo):
    code, r = wt("start", tmp_path / "nowhere", "--slug", SLUG, "--run-dir", tmp_path / "rd")
    assert code == 2 and "rev-parse" in r["error"]
    s = start(repo)
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--upstream", "a=x", "b=y")
    assert code == 2 and "--graph" in r["error"]
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--upstream", "a")
    assert code == 2 and "NODE=SHA" in r["error"]
    assert not os.path.exists(os.path.join(s["root"], "c"))  # RF-58: no worktree or branch left by a usage error
    assert sh(repo, "git", "branch", "--list", f"graph/{SLUG}/*") == ""
    code, r = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", "a=x", "b=y")
    assert code == 2 and not os.path.exists(os.path.join(s["root"], "integration"))
    code, r = wt("scope", s["baseline"], "--base", s["base"], "--commit", s["base"])
    assert code == 2 and "--writes" in r["error"]
    code, r = wt("commit", tmp_path / "nowhere", "--message", "m")
    assert code == 2


def test_start_refuses_detached_head_and_root_inside_run_dir(repo):
    code, r = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG, "--root", repo / ".graph" / SLUG / "wt")
    assert code == 3 and "inside the run directory" in r["error"]
    sh(repo, "git", "checkout", "-q", "--detach")
    code, r = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG)
    assert code == 3 and "detached" in r["error"]


def test_node_and_integrate_refuse_a_dirty_worktree(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    (pathlib.Path(na["worktree"]) / "a.txt").write_text("uncommitted\n")
    code, r = wt("node", repo, "--slug", SLUG, "--node", "a", "--attempt", 2, "--from", ca)
    assert code == 3 and "uncommitted" in r["error"]
    code, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"a={ca}")
    (pathlib.Path(ig["worktree"]) / "a.txt").write_text("dirty\n")
    code, r = wt("integrate", repo, "--slug", SLUG, "--attempt", 2, "--base", s["base"], "--accepted", f"a={ca}")
    assert code == 3 and "uncommitted" in r["error"]


def test_integrate_conflict_exits_3(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"a.txt": "b wrote a\n"})
    code, r = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"],
                 "--graph", repo / ".graph" / SLUG / "graph.yaml", "--accepted", f"a={ca}", f"b={cb}")
    assert code == 3 and r["conflicts"] == ["a.txt"]


def test_integration_is_deterministic_across_input_orders(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    _, cc = build(repo, s, "c", 1, s["base"], {"c.txt": "c v1\n"}, upstream=[f"a={ca}", f"b={cb}"])
    g = repo / ".graph" / SLUG / "graph.yaml"
    _, one = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--graph", g, "--accepted", f"a={ca}", f"b={cb}", f"c={cc}")
    _, two = wt("integrate", repo, "--slug", SLUG, "--attempt", 2, "--base", s["base"], "--graph", g, "--accepted", f"c={cc}", f"b={cb}", f"a={ca}")
    tree = lambda c: sh(repo, "git", "rev-parse", c + "^{tree}")
    assert one["order"] == two["order"] == ["a", "b", "c"] and tree(one["commit"]) == tree(two["commit"])


def test_verify_findings_w01_w02_w03_w06_w07(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    nb, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    good = lambda n, c, ch: {"branch": n["branch"], "base": n["base"], "commit": c, "changed": ch}
    d = record(repo, s, [row("node", "a", 1, {**good(na, ca, ["a.txt"]), "commit": "f" * 40})])
    assert wt("verify", d)[1]["findings"][0].startswith("W01 a#1")
    record(repo, s, [row("node", "a", 1, {**good(na, ca, ["a.txt", "b.txt"]), "base": cb})])
    assert any(f.startswith("W02 a#1") for f in wt("verify", d)[1]["findings"])
    _, ca2 = build(repo, s, "a", 2, ca, {"a.txt": "a v2\n"})
    record(repo, s, [row("node", "a", 1, {**good(na, ca, ["a.txt"]), "branch": f"graph/{SLUG}/a/a2"})])
    assert any(f.startswith("W03 a#1") for f in wt("verify", d)[1]["findings"])
    s2 = {**s, "base": ca}  # a run base that node b does not descend from
    d = record(repo, s2, [row("node", "b", 1, good(nb, cb, ["b.txt"]))])
    assert any(f.startswith("W06 b") for f in wt("verify", d)[1]["findings"])
    d = record(repo, s, [row("node", "b", 1, good(nb, cb, ["b.txt"]))], landed={"kind": "fast_forward", "commit": cb})
    assert any(f.startswith("W07 landed") for f in wt("verify", d)[1]["findings"])


def test_verify_without_worktree_kind_is_a_no_op(repo, tmp_path):
    d = tmp_path / "rd"; d.mkdir()
    (d / "checks.yaml").write_text("rows: []\n")
    (d / "progress.yaml").write_text(yaml.safe_dump({"workspace": {"kind": "directory", "reason": "no git"}}))
    code, r = wt("verify", d, "--repo", repo)
    assert code == 0 and r["findings"] == []


def test_land_refuses_another_checked_out_branch_and_cleanup_all_clean(repo):
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    sh(repo, "git", "checkout", "-q", "-b", "other")
    code, ld = wt("land", repo, "--commit", ca, "--branch", "main")
    assert code == 5 and "other" in ld["reason"]
    code, cl = wt("cleanup", repo, "--root", s["root"])
    assert code == 0 and cl["kept"] == [] and len(cl["removed"]) == 2 and not os.path.exists(s["root"])


def test_rf62_retry_that_undoes_an_out_of_scope_write_is_in_scope(repo):
    s = start(repo)
    n1, c1 = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n", "a.txt": "escaped\n"})
    code, _ = wt("scope", n1["worktree"], "--base", s["base"], "--commit", c1, "--writes", "b.txt")
    assert code == 1
    n2, c2 = build(repo, s, "b", 2, c1, {"b.txt": "b v2\n", "a.txt": "a.txt v0\n"})  # the retry restores a.txt
    code, per_attempt = wt("scope", n2["worktree"], "--base", n2["base"], "--commit", c2, "--writes", "b.txt")
    assert code == 1 and per_attempt["outside"] == ["a.txt"]  # measured per attempt, the fix itself is out of scope
    code, sc = wt("scope", n2["worktree"], "--base", s["base"], "--commit", c2, "--writes", "b.txt")
    assert code == 0 and sc["changed"] == ["b.txt"]  # measured from the scope base, it is not


def test_rf61_exclude_keeps_gate_byproducts_out_of_commits(repo):
    code, s = wt("start", repo, "--slug", SLUG, "--run-dir", repo / ".graph" / SLUG, "--exclude", "__pycache__/")
    assert code == 0 and s["excluded"] == ["__pycache__/"]
    n, c = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n", "pkg/__pycache__/m.pyc": "x"})
    code, sc = wt("scope", n["worktree"], "--base", s["base"], "--commit", c, "--writes", "a.txt")
    assert code == 0 and sc["changed"] == ["a.txt"]
    code, r = wt("exclude", repo, "__pycache__/", "*.log")
    assert code == 0 and r["added"] == ["*.log"]


def test_rf63_verify_reads_the_bundled_record_layout(repo):
    """verify must read progress.yaml the way validate.py does: no wrapper key."""
    ex = HERE.parent.parent / "graph-record" / "scripts" / "example-worktree"
    code, r = wt("verify", ex, "--repo", repo)
    assert code == 1 and r["findings"] and "note" not in r  # synthetic commits are not in this repo: W01, not a silent no-op


def test_rf64_repeated_list_flags_accumulate(repo):
    """A fresh lead wrote --upstream a=X --upstream b=Y; both must be merged, not only the last."""
    s = start(repo)
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    code, n = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"],
                 "--graph", repo / ".graph" / SLUG / "graph.yaml", "--upstream", f"a={ca}", "--upstream", f"b={cb}")
    assert code == 0
    tree = pathlib.Path(n["worktree"])
    assert (tree / "a.txt").read_text() == "a v1\n" and (tree / "b.txt").read_text() == "b v1\n"


# T-49 (run 13): tests for the mutation survivors classified as test gaps ----------

@pytest.mark.parametrize("pairs", [["=abc"], ["a="], ["a=x", "a=y"]])
def test_gap_malformed_or_duplicate_pairs_exit_2(repo, pairs):
    s = start(repo)
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--upstream", *pairs)
    assert code == 2 and "NODE=SHA" in r["error"]


def test_gap_cycle_and_unknown_nodes(repo, tmp_path):
    s = start(repo)
    cyc = tmp_path / "cycle.yaml"
    cyc.write_text(yaml.safe_dump({"nodes": [
        {"id": "a", "reads": {"upstream": [{"node": "b"}]}, "writes": ["a.txt"]},
        {"id": "b", "reads": {"upstream": [{"node": "a"}]}, "writes": ["b.txt"]}]}))
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--graph", cyc, "--upstream", "a=x", "b=y")
    assert code == 3 and "cycle" in r["error"]
    g = repo / ".graph" / SLUG / "graph.yaml"
    code, r = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--graph", g, "--upstream", "a=x", "zz=y")
    assert code == 2 and "zz" in r["error"]
    code, r = wt("scope", s["baseline"], "--base", s["base"], "--commit", s["base"], "--graph", g, "--node", "zz")
    assert code == 2 and "not a graph node" in r["error"]
    code, r = wt("scope", s["baseline"], "--base", s["base"], "--commit", s["base"], "--graph", g)
    assert code == 2 and "--writes" in r["error"]


def test_gap_scope_prefix_needs_trailing_slash(repo):
    s = start(repo)
    n, c = build(repo, s, "a", 1, s["base"], {"docs/x.md": "x\n"})
    assert wt("scope", n["worktree"], "--base", s["base"], "--commit", c, "--writes", "docs")[1]["outside"] == ["docs/x.md"]
    assert wt("scope", n["worktree"], "--base", s["base"], "--commit", c, "--writes", "docs/")[1]["outside"] == []


def test_gap_w07_missing_person_branch(repo):
    s = start(repo)
    nb, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    d = record(repo, {**s}, [row("node", "b", 1, {"branch": nb["branch"], "base": nb["base"], "commit": cb, "changed": ["b.txt"]})],
               landed={"kind": "fast_forward", "commit": cb})
    p = yaml.safe_load((d / "progress.yaml").read_text()); p["workspace"]["person_branch"] = "gone"
    (d / "progress.yaml").write_text(yaml.safe_dump(p))
    assert any(f.startswith("W07 landed") for f in wt("verify", d)[1]["findings"])


def test_gap_w02_scope_base_must_exist_and_be_an_ancestor(repo):
    s = start(repo)
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    w = {"branch": na["branch"], "base": na["base"], "commit": ca, "changed": ["a.txt"]}
    d = record(repo, s, [row("node", "a", 1, {**w, "scope_base": cb})])
    assert any(f.startswith("W02 a#1") for f in wt("verify", d)[1]["findings"])
    record(repo, s, [row("node", "a", 1, {**w, "scope_base": "e" * 40})])
    assert any(f.startswith("W02 a#1") for f in wt("verify", d)[1]["findings"])
    record(repo, s, [row("node", "a", 1, {**w, "scope_base": s["base"]})])
    assert wt("verify", d)[1]["findings"] == []
