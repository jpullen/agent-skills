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


def test_rf67_rebuild_keeps_the_nodes_own_changes_in_the_scope_diff(repo):
    """A rebuild on a re-accepted upstream must not hide what the node itself changed earlier."""
    s = start(repo)
    g = repo / ".graph" / SLUG / "graph.yaml"
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    _, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    n1, c1 = build(repo, s, "c", 1, s["base"], {"c.txt": "c v1\n", "stray.txt": "outside writes\n"}, upstream=[f"a={ca}", f"b={cb}"])
    _, ca2 = build(repo, s, "a", 2, ca, {"a.txt": "a v2\n"})
    code, n2 = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 2, "--from", s["base"], "--graph", g,
                  "--upstream", f"a={ca2}", "--upstream", f"b={cb}", "--carry", c1)
    assert code == 0 and n2["upstream_base"] != n2["base"]
    tree = pathlib.Path(n2["worktree"])
    assert (tree / "a.txt").read_text() == "a v2\n" and (tree / "c.txt").read_text() == "c v1\n"
    code, hidden = wt("scope", tree, "--base", n2["base"], "--commit", n2["base"], "--writes", "c.txt")
    assert code == 0 and hidden["changed"] == []                       # measured from the rebuilt base, the stray write is invisible
    code, sc = wt("scope", tree, "--base", n2["upstream_base"], "--commit", n2["base"], "--writes", "c.txt")
    assert code == 1 and sc["outside"] == ["stray.txt"]                # measured from the upstream base, it is caught
    w2 = {"branch": n2["branch"], "base": n2["base"], "scope_base": n2["upstream_base"], "commit": n2["base"], "changed": ["c.txt", "stray.txt"]}
    w1 = {"branch": n1["branch"], "base": n1["base"], "scope_base": n1["base"], "commit": c1, "changed": ["c.txt", "stray.txt"]}
    d = record(repo, s, [row("node", "c", 1, w1, "fail"), row("node", "c", 2, w2, "fail")])
    assert wt("verify", d)[1]["findings"] == []
    record(repo, s, [row("node", "c", 1, {**w1, "commit": cb, "branch": f"graph/{SLUG}/b/a1", "changed": ["b.txt"], "base": s["base"], "scope_base": s["base"]}, "fail"),
                     row("node", "c", 2, {**w2, "base": n2["upstream_base"], "commit": n2["upstream_base"], "changed": [], "branch": n2["branch"]}, "fail")])
    assert any(f.startswith("W03") or f.startswith("W08") for f in wt("verify", d)[1]["findings"])


def test_w08_previous_attempt_must_be_contained_in_the_next_base(repo):
    s = start(repo)
    n1, c1 = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    sh(repo, "git", "branch", f"graph/{SLUG}/a/a2", s["base"])           # a second attempt that silently dropped the first
    d = record(repo, s, [row("node", "a", 1, {"branch": n1["branch"], "base": s["base"], "scope_base": s["base"], "commit": c1, "changed": ["a.txt"]}, "fail"),
                         row("node", "a", 2, {"branch": f"graph/{SLUG}/a/a2", "base": s["base"], "scope_base": s["base"], "commit": s["base"], "changed": []}, "fail")])
    assert any(f.startswith("W08 a#2") for f in wt("verify", d)[1]["findings"])


# Run 14 (the publishing run): RF-73 history gate and squash landing, RF-74 author check ---------

AUTHOR = "Test <test@example.invalid>"


def test_rf74_commit_refuses_a_reset_git_identity(repo):
    s = start(repo)
    code, n = wt("node", repo, "--slug", SLUG, "--node", "a", "--attempt", 1, "--from", s["base"])
    (pathlib.Path(n["worktree"]) / "a.txt").write_text("a v1\n")
    sh(repo, "git", "config", "user.name", "Claude")                     # what a container restart left behind
    code, r = wt("commit", n["worktree"], "--message", "a a1", "--author", AUTHOR)
    assert code == 3 and r["actual"] == "Claude <test@example.invalid>" and r["expected"] == AUTHOR
    assert sh(n["worktree"], "git", "log", "--format=%s", "-1") == "init"  # nothing was committed
    sh(repo, "git", "config", "user.name", "Test")
    code, r = wt("commit", n["worktree"], "--message", "a a1", "--author", AUTHOR)
    assert code == 0


def test_rf73_history_lists_and_gates_every_commit_a_push_would_publish(repo):
    s = start(repo)
    _, c1 = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n", "a.txt": "SECRET\n"})   # a failed attempt
    _, c2 = build(repo, s, "b", 2, c1, {"b.txt": "b v1\n", "a.txt": "a.txt v0\n"})        # the retry removes it
    code, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"b={c2}")
    assert "SECRET" not in (pathlib.Path(ig["worktree"]) / "a.txt").read_text()            # the tree is clean...
    code, h = wt("history", repo, "--base", s["base"], "--commit", ig["commit"])
    assert code == 0 and h["count"] == 2 and h["commits"][0]["paths"] == ["a.txt", "b.txt"] and h["commits"][0]["author"] == AUTHOR
    code, h = wt("history", repo, "--base", s["base"], "--commit", ig["commit"], "--exec", "! grep -rq SECRET --exclude-dir=.git")
    assert code == 1 and h["failed"] == [c1]                                               # ...the history is not
    assert all("history-" not in line for line in sh(repo, "git", "worktree", "list").splitlines())
    code, h = wt("history", repo, "--base", c1, "--commit", ig["commit"], "--exec", "! grep -rq SECRET --exclude-dir=.git")
    assert code == 0 and h["count"] == 1


def squash_record(repo, s, ig, c, landed, author=None):
    d = record(repo, s, [row("node", "b", 1, {"branch": f"graph/{SLUG}/b/a1", "base": s["base"], "scope_base": s["base"], "commit": c, "changed": ["b.txt"]}),
                         row("integration", None, 1, {"branch": ig["branch"], "base": s["base"], "scope_base": s["base"], "commit": ig["commit"], "changed": ["b.txt"]})],
               ig["branch"], landed)
    p = yaml.safe_load((d / "progress.yaml").read_text()); p["graph"]["accepted"] = ["b"]
    if author:
        p["workspace"]["author"] = author
    (d / "progress.yaml").write_text(yaml.safe_dump(p))
    return d


def test_rf73_squash_landing_publishes_one_commit(repo):
    s = start(repo)
    _, c = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    _, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"b={c}")
    code, r = wt("land", repo, "--commit", ig["commit"], "--branch", "main", "--squash")
    assert code == 2 and "--base" in r["error"]
    code, ld = wt("land", repo, "--commit", ig["commit"], "--branch", "main", "--squash", "--base", s["base"], "--message", "units: deliver", "--author", AUTHOR)
    assert code == 0 and ld["kind"] == "squashed" and ld["commit"] != ig["commit"]
    assert sh(repo, "git", "rev-list", f"{s['base']}..main").splitlines() == [ld["commit"]]   # one commit, no attempt history
    assert (repo / "b.txt").read_text() == "b v1\n"
    d = squash_record(repo, s, ig, c, ld, AUTHOR)
    assert wt("verify", d) == (0, {"findings": []})
    squash_record(repo, s, ig, c, {"kind": "squashed", "commit": s["base"]})                  # the base is not a squash of the integration tree
    assert any(f.startswith("W09 landed") for f in wt("verify", d)[1]["findings"])
    squash_record(repo, s, ig, c, ld, "Someone Else <else@example.invalid>")
    assert any(f.startswith("W10") for f in wt("verify", d)[1]["findings"])


def test_rf73_squash_refuses_a_moved_branch(repo):
    s = start(repo)
    _, c = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    (repo / "c.txt").write_text("person moved on\n"); sh(repo, "git", "commit", "-qam", "person")
    code, ld = wt("land", repo, "--commit", c, "--branch", "main", "--squash", "--base", s["base"], "--message", "m")
    assert code == 5 and ld["kind"] == "not_landed" and "run base" in ld["reason"]


# Mutation survivors in the run-14 code, each a test gap -------------------------------------

def test_gap_squash_needs_both_base_and_message_and_a_clean_checkout(repo):
    s = start(repo)
    _, c = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    code, r = wt("land", repo, "--commit", c, "--branch", "main", "--squash", "--base", s["base"])
    assert code == 2 and "--message" in r["error"]
    (repo / "b.txt").write_text("the person's uncommitted edit\n")
    code, ld = wt("land", repo, "--commit", c, "--branch", "main", "--squash", "--base", s["base"], "--message", "m")
    assert code == 5 and ld["kind"] == "not_landed" and "could not be checked out" in ld["reason"]
    assert (repo / "b.txt").read_text() == "the person's uncommitted edit\n"


def test_gap_w09_squash_with_the_right_parent_and_the_wrong_tree(repo):
    s = start(repo)
    _, c = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    _, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"b={c}")
    other = sh(repo, "git", "commit-tree", s["base"] + "^{tree}", "-p", s["base"], "-m", "not the integration tree")
    sh(repo, "git", "merge", "-q", "--ff-only", other)
    d = squash_record(repo, s, ig, c, {"kind": "squashed", "commit": other})
    assert [f[:3] for f in wt("verify", d)[1]["findings"]] == ["W09"]


def test_gap_w10_finds_a_wrong_author_on_an_attempt_and_on_an_integration_merge(repo):
    s = start(repo)
    g = repo / ".graph" / SLUG / "graph.yaml"
    na, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    nb, cb = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    w = lambda n, c, p: {"branch": n["branch"], "base": n["base"], "scope_base": n["base"], "commit": c, "changed": [p]}
    rows = [row("node", "a", 1, w(na, ca, "a.txt")), row("node", "b", 1, w(nb, cb, "b.txt"))]

    def author(d):
        p = yaml.safe_load((d / "progress.yaml").read_text()); p["workspace"]["author"] = AUTHOR; p["graph"]["accepted"] = ["a", "b"]
        (d / "progress.yaml").write_text(yaml.safe_dump(p)); return d
    assert wt("verify", author(record(repo, s, rows)))[1]["findings"] == []     # no integration yet: attempts alone are checked
    sh(repo, "git", "config", "user.name", "Claude")                             # the identity is reset before integration
    _, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--graph", g, "--accepted", f"a={ca}", f"b={cb}")
    rows.append(row("integration", None, 1, {"branch": ig["branch"], "base": s["base"], "scope_base": s["base"], "commit": ig["commit"], "changed": ["a.txt", "b.txt"]}))
    found = wt("verify", author(record(repo, s, rows, ig["branch"])))[1]["findings"]
    assert len(found) == 1 and found[0].startswith(f"W10 {ig['commit'][:12]}")   # only the merge commit
    nb2, cb2 = build(repo, s, "b", 2, cb, {"b.txt": "b v2\n"})                   # and a later attempt, outside the integration
    rows.insert(2, row("node", "b", 2, {"branch": nb2["branch"], "base": cb, "scope_base": s["base"], "commit": cb2, "changed": ["b.txt"]}, "fail"))
    found = wt("verify", author(record(repo, s, rows, ig["branch"])))[1]["findings"]
    assert sorted(f[:16] for f in found if f.startswith("W10")) == sorted([f"W10 {ig['commit'][:12]}", f"W10 {cb2[:12]}"])


def test_rf79_history_forbid_reads_messages_and_authors(repo):
    """Run 15: the tree check passed on every commit; nothing read the commit messages or author lines a push also publishes."""
    s = start(repo)
    n, _ = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    (pathlib.Path(n["worktree"]) / "a.txt").write_text("a v2\n")
    sh(n["worktree"], "git", "commit", "-qam", "a: fix per the Falcon review")
    tip = sh(n["worktree"], "git", "rev-parse", "HEAD")
    code, h = wt("history", repo, "--base", s["base"], "--commit", tip, "--exec", "true", "--forbid", "falcon|corp\\.example")
    assert code == 1 and h["failed"] == [tip] and h["commits"][1]["forbidden"] is True and "forbidden" not in h["commits"][0]
    code, h = wt("history", repo, "--base", s["base"], "--commit", tip, "--forbid", "example\\.invalid")     # the author line
    assert code == 1 and len(h["failed"]) == 2
    assert wt("history", repo, "--base", s["base"], "--commit", tip, "--forbid", "nothing-like-this")[0] == 0
    code, r = wt("history", repo, "--base", s["base"], "--commit", tip, "--forbid", "(")
    assert code == 2 and "regular expression" in r["error"]


# Codex review of the release commit: one test per finding ---------------------------------------------------

def test_review_env_author_is_the_author_git_writes(repo):
    s = start(repo)
    code, n = wt("node", repo, "--slug", SLUG, "--node", "a", "--attempt", 1, "--from", s["base"])
    (pathlib.Path(n["worktree"]) / "a.txt").write_text("a v1\n")
    env = dict(os.environ, GIT_AUTHOR_NAME="Env", GIT_AUTHOR_EMAIL="env@example.invalid")
    r = subprocess.run([sys.executable, str(SCRIPT), "commit", n["worktree"], "--message", "m", "--author", AUTHOR], capture_output=True, text=True, env=env)
    assert r.returncode == 3 and json.loads(r.stdout)["actual"] == "Env <env@example.invalid>"
    assert sh(n["worktree"], "git", "log", "-1", "--format=%s") == "init"
    r = subprocess.run([sys.executable, str(SCRIPT), "land", repo, "--commit", s["base"], "--branch", "main", "--squash", "--base", s["base"],
                        "--message", "m", "--author", AUTHOR], capture_output=True, text=True, env=env)
    assert r.returncode == 3


def test_review_rename_source_is_outside_writes(repo):
    s = start(repo)
    code, n = wt("node", repo, "--slug", SLUG, "--node", "b", "--attempt", 1, "--from", s["base"])
    sh(n["worktree"], "git", "mv", "a.txt", "b-renamed.txt")
    code, c = wt("commit", n["worktree"], "--message", "rename")
    code, sc = wt("scope", n["worktree"], "--base", s["base"], "--commit", c["commit"], "--writes", "b-renamed.txt")
    assert code == 1 and sc["outside"] == ["a.txt"] and sorted(sc["changed"]) == ["a.txt", "b-renamed.txt"]


@pytest.mark.parametrize("name", ["integration", "baseline", "history-1"])
def test_review_reserved_node_names_are_refused(repo, name):
    s = start(repo)
    code, r = wt("node", repo, "--slug", SLUG, "--node", name, "--attempt", 1, "--from", s["base"])
    assert code == 2 and "reserved" in r["error"]
    assert sh(repo, "git", "branch", "--list", f"graph/{SLUG}/{name}/*") == ""


def test_review_history_tree_path_with_spaces(tmp_path):
    spaced = tmp_path / "a dir; with $pecial"
    spaced.mkdir()
    r = spaced / "repo"; r.mkdir()
    sh(r, "git", "init", "-q", "-b", "main"); sh(r, "git", "config", "user.name", "Test"); sh(r, "git", "config", "user.email", "test@example.invalid")
    (r / "f.txt").write_text("1\n"); sh(r, "git", "add", "-A"); sh(r, "git", "commit", "-qm", "one")
    base = sh(r, "git", "rev-parse", "HEAD")
    (r / "f.txt").write_text("2\n"); sh(r, "git", "commit", "-qam", "two")
    code, h = wt("history", r, "--base", base, "--commit", "HEAD", "--exec", "test -d")
    assert code == 0 and h["failed"] == []


def test_review_history_checks_each_commit_in_a_clean_tree(repo):
    """Python's bytecode cache keyed on mtime and size let a commit's check read the previous commit's module."""
    s = start(repo)
    (repo / "payload.py").write_text('VALUE = "public"\n'); sh(repo, "git", "add", "payload.py"); sh(repo, "git", "commit", "-qm", "public")
    (repo / "payload.py").write_text('VALUE = "SECRET"\n'); sh(repo, "git", "commit", "-qam", "secret")
    tip = sh(repo, "git", "rev-parse", "HEAD")
    check = "env -u PYTHONDONTWRITEBYTECODE python3 -c \"import sys; sys.path.insert(0, '.'); import payload; sys.exit(payload.VALUE == 'SECRET')\" #"
    code, h = wt("history", repo, "--base", s["base"], "--commit", tip, "--exec", check)
    assert code == 1 and h["failed"] == [tip]


def test_review_no_op_carry_validates_and_w11_guards_the_real_case(repo):
    """A rebuild whose previous attempt changed nothing has base == upstream_base; that is valid. The RF-67 case — a scope
    base that holds the node's own earlier work — is now caught by verify W11 rather than by an equality rule."""
    s = start(repo)
    g = repo / ".graph" / SLUG / "graph.yaml"
    _, ca = build(repo, s, "a", 1, s["base"], {"a.txt": "a v1\n"})
    code, n1 = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 1, "--from", s["base"], "--graph", g, "--upstream", f"a={ca}")
    assert wt("commit", n1["worktree"], "--message", "c a1")[0] == 4                 # changed nothing: commit is its base
    _, ca2 = build(repo, s, "a", 2, ca, {"a.txt": "a v2\n"})
    code, n2 = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 2, "--from", s["base"], "--graph", g, "--upstream", f"a={ca2}", "--carry", n1["base"])
    assert code == 0 and n2["base"] == n2["upstream_base"]                            # the carry was a no-op
    w1 = {"branch": n1["branch"], "base": n1["base"], "scope_base": n1["base"], "commit": n1["base"], "changed": []}
    w2 = {"branch": n2["branch"], "base": n2["base"], "scope_base": n2["upstream_base"], "commit": n2["base"], "changed": []}
    d = record(repo, s, [row("node", "c", 1, w1, "fail"), row("node", "c", 2, w2, "fail")])
    assert wt("verify", d)[1]["findings"] == []
    n3, c3 = build(repo, s, "c", 3, n2["base"], {"c.txt": "c v3\n"})
    _, ca3 = build(repo, s, "a", 3, ca2, {"a.txt": "a v3\n"})
    code, n4 = wt("node", repo, "--slug", SLUG, "--node", "c", "--attempt", 4, "--from", s["base"], "--graph", g, "--upstream", f"a={ca3}", "--carry", c3)
    w3 = {"branch": n3["branch"], "base": n3["base"], "scope_base": n2["upstream_base"], "commit": c3, "changed": ["c.txt"]}
    hiding = {"branch": n4["branch"], "base": n4["base"], "scope_base": n4["base"], "commit": n4["base"], "changed": []}
    record(repo, s, [row("node", "c", 1, w1, "fail"), row("node", "c", 2, w2, "fail"), row("node", "c", 3, w3, "fail"), row("node", "c", 4, hiding, "fail")])
    assert any(f.startswith("W11 c#4") for f in wt("verify", d)[1]["findings"])


def test_review_w10_scans_a_squashed_landing(repo):
    s = start(repo)
    _, c = build(repo, s, "b", 1, s["base"], {"b.txt": "b v1\n"})
    _, ig = wt("integrate", repo, "--slug", SLUG, "--attempt", 1, "--base", s["base"], "--accepted", f"b={c}")
    env = dict(os.environ, GIT_AUTHOR_NAME="Env", GIT_AUTHOR_EMAIL="env@example.invalid")
    squashed = subprocess.run(["git", "-C", str(repo), "commit-tree", ig["commit"] + "^{tree}", "-p", s["base"], "-m", "deliver"],
                              capture_output=True, text=True, env=env, check=True).stdout.strip()
    sh(repo, "git", "merge", "-q", "--ff-only", squashed)
    d = squash_record(repo, s, ig, c, {"kind": "squashed", "commit": squashed}, AUTHOR)
    found = wt("verify", d)[1]["findings"]
    assert [f[:16] for f in found] == [f"W10 {squashed[:12]}"]
