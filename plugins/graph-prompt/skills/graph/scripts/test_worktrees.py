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
    (d / "progress.yaml").write_text(yaml.safe_dump({"progress": {"workspace": ws, "graph": {"accepted": ["a", "b", "c"], "dissent": []}}}))
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
