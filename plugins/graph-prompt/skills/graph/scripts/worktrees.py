#!/usr/bin/env python3
"""worktrees.py — the git worktree machinery of a graph-prompt v3.6 run (D67-D70).

Every step here is deterministic, so it runs as a program, never as a subagent
(layer_3). The lead calls it; builders never do.

  start     REPO --slug S --run-dir D [--root DIR] [--scope P ...]
            record the run base (HEAD), check the scope paths are clean, keep the
            run directory out of every worktree, create the baseline worktree.
  node      REPO --slug S --node N --attempt K --from SHA [--upstream U=SHA ...] [--graph G]
            create (or switch) the node's worktree onto branch graph/S/N/aK at SHA,
            then merge the upstream commits in topological order (ties by node id).
  commit    WORKTREE --message M
            stage everything in the worktree and commit it; one commit per attempt.
  scope     WORKTREE --base B --commit C (--writes P ... | --graph G --node N)
            list the paths the attempt changed and those outside the node's writes.
  integrate REPO --slug S --attempt K --base B0 --graph G --accepted N=SHA ...
            build graph/S/integration/aK from B0 by merging every accepted node's
            newest commit in topological order; confirm each is an ancestor.
  verify    RUN_DIR --repo REPO
            check every row's workspace against git: commits exist, base is an
            ancestor, branch tip and changed list agree, integration converges.
  land      REPO --commit C --branch PB
            fast-forward the person's branch to C; anything but a fast-forward is
            not landed.
  cleanup   REPO --root DIR
            remove the run's clean worktrees (never --force); branches are kept.

Output is one JSON object on stdout. Exit codes: 0 done; 1 findings (scope
outside writes, verify findings, a worktree kept by cleanup); 2 usage or git
error; 3 precondition failed or merge conflict (the merge is aborted); 4 nothing
to commit; 5 not landed.
"""
import argparse
import json
import os
import subprocess
import sys

import yaml


class Fail(Exception):
    def __init__(self, code, payload):
        super().__init__(payload)
        self.code, self.payload = code, payload


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise Fail(2, {"error": f"git {' '.join(args)}", "stderr": r.stderr.strip()})
    return r


def out(repo, *args):
    return git(repo, *args).stdout.strip()


def is_ancestor(repo, a, b):
    return git(repo, "merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def topo_order(graph_path):
    """Kahn's algorithm over reads.upstream edges; ready nodes are taken in id order."""
    with open(graph_path, encoding="utf-8") as fh:
        nodes = yaml.safe_load(fh)["nodes"]
    ups = {n["id"]: {u["node"] for u in n["reads"]["upstream"]} for n in nodes}
    order, done = [], set()
    while len(order) < len(ups):
        ready = sorted(n for n, u in ups.items() if n not in done and u <= done)
        if not ready:
            raise Fail(3, {"error": "reads graph has a cycle"})
        order.append(ready[0]); done.add(ready[0])
    return order, {n["id"]: n for n in nodes}


def parse_pairs(pairs):
    res = {}
    for p in pairs or []:
        k, sep, v = p.partition("=")
        if not sep or not k or not v or k in res:
            raise Fail(2, {"error": f"expected unique NODE=SHA, got {p!r}"})
        res[k] = v
    return res


def ordered(pairs, graph):
    if len(pairs) < 2:
        return list(pairs.items())
    if not graph:
        raise Fail(2, {"error": "--graph is required to order two or more commits"})
    order, _ = topo_order(graph)
    unknown = sorted(set(pairs) - set(order))
    if unknown:
        raise Fail(2, {"error": f"not graph nodes: {unknown}"})
    return [(n, pairs[n]) for n in order if n in pairs]


def merge_all(wt, commits, label):
    for name, sha in commits:
        r = git(wt, "merge", "--no-edit", "-m", f"{label} <- {name}", sha, check=False)
        if r.returncode != 0:
            conflicts = out(wt, "diff", "--name-only", "--diff-filter=U").splitlines()
            git(wt, "merge", "--abort", check=False)
            raise Fail(3, {"error": "merge conflict", "merging": name, "commit": sha, "conflicts": conflicts,
                           "stderr": r.stderr.strip()})


def default_root(repo, slug):
    common = out(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return os.path.join(common, "graph-worktrees", slug)


def cmd_start(a):
    top = out(a.repo, "rev-parse", "--show-toplevel")
    branch = git(top, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch.returncode != 0:
        raise Fail(3, {"error": "HEAD is detached; a run lands on a named branch"})
    base = out(top, "rev-parse", "HEAD")
    if a.scope:
        dirty = git(top, "status", "--porcelain", "--", *a.scope).stdout.splitlines()
        if dirty:
            raise Fail(3, {"error": "uncommitted changes inside the scope", "paths": dirty})
    run_dir = os.path.abspath(a.run_dir)
    rel = os.path.relpath(run_dir, top)
    if not rel.startswith(".."):
        if out(top, "ls-files", "--", rel):
            raise Fail(3, {"error": "the run directory is tracked; every worktree would carry the record and its gate programs", "run_dir": rel})
        if git(top, "check-ignore", "-q", rel + "/", check=False).returncode != 0:
            exclude = os.path.join(out(top, "rev-parse", "--path-format=absolute", "--git-common-dir"), "info", "exclude")
            os.makedirs(os.path.dirname(exclude), exist_ok=True)
            with open(exclude, "a", encoding="utf-8") as fh:
                fh.write(f"/{rel.replace(os.sep, '/')}/\n")
    root = os.path.abspath(a.root) if a.root else default_root(top, a.slug)
    if os.path.relpath(root, run_dir).split(os.sep)[0] != "..":
        raise Fail(3, {"error": "the worktree root is inside the run directory", "root": root})
    if os.path.exists(root):
        raise Fail(3, {"error": "the worktree root already exists; a run creates its own", "root": root})
    os.makedirs(os.path.dirname(root), exist_ok=True)
    git(top, "worktree", "add", "--detach", os.path.join(root, "baseline"), base)
    return 0, {"kind": "worktree", "repo": top, "base": base, "person_branch": branch.stdout.strip(),
               "root": root, "baseline": os.path.join(root, "baseline")}


def cmd_node(a):
    root = os.path.abspath(a.root) if a.root else default_root(a.repo, a.slug)
    wt = os.path.join(root, a.node)
    branch = f"graph/{a.slug}/{a.node}/a{a.attempt}"
    start = out(a.repo, "rev-parse", "--verify", a.from_ + "^{commit}")
    if os.path.isdir(wt):
        if out(wt, "status", "--porcelain"):
            raise Fail(3, {"error": "the node's worktree has uncommitted changes", "worktree": wt})
        git(wt, "switch", "-c", branch, start)
    else:
        git(a.repo, "worktree", "add", "-b", branch, wt, start)
    merge_all(wt, ordered(parse_pairs(a.upstream), a.graph), f"graph({a.slug}): {a.node} a{a.attempt} base")
    return 0, {"worktree": wt, "branch": branch, "base": out(wt, "rev-parse", "HEAD")}


def cmd_commit(a):
    git(a.worktree, "add", "-A")
    if git(a.worktree, "diff", "--cached", "--quiet", check=False).returncode == 0:
        raise Fail(4, {"error": "nothing to commit", "worktree": a.worktree})
    git(a.worktree, "commit", "-q", "-m", a.message)
    return 0, {"commit": out(a.worktree, "rev-parse", "HEAD"), "branch": out(a.worktree, "rev-parse", "--abbrev-ref", "HEAD")}


def in_writes(path, writes):
    return any(path == w or (w.endswith("/") and path.startswith(w)) for w in writes)


def cmd_scope(a):
    if a.writes:
        writes = a.writes
    elif a.graph and a.node:
        _, nodes = topo_order(a.graph)
        if a.node not in nodes:
            raise Fail(2, {"error": f"{a.node} is not a graph node"})
        writes = nodes[a.node]["writes"]
    else:
        raise Fail(2, {"error": "give --writes, or --graph with --node"})
    changed = out(a.worktree, "diff", "--name-only", a.base, a.commit).splitlines()
    outside = [p for p in changed if not in_writes(p, writes)]
    return (1 if outside else 0), {"changed": changed, "outside": outside, "writes": writes}


def cmd_integrate(a):
    root = os.path.abspath(a.root) if a.root else default_root(a.repo, a.slug)
    wt = os.path.join(root, "integration")
    branch = f"graph/{a.slug}/integration/a{a.attempt}"
    if os.path.isdir(wt):
        if out(wt, "status", "--porcelain"):
            raise Fail(3, {"error": "the integration worktree has uncommitted changes", "worktree": wt})
        git(wt, "switch", "-c", branch, a.base)
    else:
        git(a.repo, "worktree", "add", "-b", branch, wt, a.base)
    accepted = ordered(parse_pairs(a.accepted), a.graph)
    merge_all(wt, accepted, f"graph({a.slug}): integration a{a.attempt}")
    head = out(wt, "rev-parse", "HEAD")
    missing = [n for n, sha in accepted if not is_ancestor(wt, sha, head)]
    if missing:
        raise Fail(3, {"error": "accepted commits not contained in the integration commit", "nodes": missing})
    return 0, {"worktree": wt, "branch": branch, "base": a.base, "commit": head,
               "changed": out(wt, "diff", "--name-only", a.base, head).splitlines(),
               "order": [n for n, _ in accepted]}


def cmd_verify(a):
    def y(name):
        p = os.path.join(a.run_dir, f"{name}.yaml")
        with open(p, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    rows = y("checks").get("rows", [])
    prog = y("progress").get("progress", {})
    ws = prog.get("workspace") or {}
    findings = []
    if ws.get("kind") != "worktree":
        return 0, {"findings": [], "note": "progress.workspace.kind is not worktree; nothing to verify"}
    repo = a.repo or ws.get("repo")
    exists = lambda sha: git(repo, "cat-file", "-e", sha + "^{commit}", check=False).returncode == 0
    newest = {}
    for r in rows:
        w = r.get("workspace")
        if not w:
            continue
        s = r["subject"]
        who = f"{s.get('node') or s.get('item') or s['kind']}#{r['attempt']}"
        if not exists(w["commit"]) or not exists(w["base"]):
            findings.append(f"W01 {who}: commit or base not in the repository"); continue
        if not is_ancestor(repo, w["base"], w["commit"]):
            findings.append(f"W02 {who}: base is not an ancestor of commit")
        tip = git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/" + w["branch"], check=False).stdout.strip()
        if tip != w["commit"]:
            findings.append(f"W03 {who}: branch {w['branch']} tip is {tip[:12] or 'missing'}, not the recorded commit")
        diff = set(out(repo, "diff", "--name-only", w["base"], w["commit"]).splitlines())
        if diff != set(w["changed"]):
            findings.append(f"W04 {who}: changed list differs from git diff (git has {sorted(diff ^ set(w['changed']))} different)")
        if s["kind"] == "node" and r["verdict"] in ("pass", "dissent"):
            cur = newest.get(s["node"])
            if not cur or r["attempt"] > cur[0]:
                newest[s["node"]] = (r["attempt"], w["commit"])
        if s["kind"] in ("acceptance", "integration"):
            cur = newest.get(None)
            if not cur or r["attempt"] > cur[0]:
                newest[None] = (r["attempt"], w["commit"])
    integ = newest.pop(None, None)
    accepted = set(prog.get("graph", {}).get("accepted", [])) | set(prog.get("graph", {}).get("dissent", []))
    if integ:
        for node in sorted(accepted):
            if node in newest and exists(newest[node][1]) and not is_ancestor(repo, newest[node][1], integ[1]):
                findings.append(f"W05 {node}: newest accepted commit is not contained in integration attempt {integ[0]}")
    if exists(ws.get("base", "0" * 40)):
        for node, (_, sha) in sorted(newest.items()):
            if exists(sha) and not is_ancestor(repo, ws["base"], sha):
                findings.append(f"W06 {node}: newest accepted commit does not descend from the run base")
    landed = ws.get("landed") or {}
    if landed.get("kind") == "fast_forward":
        tip = git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/" + ws.get("person_branch", ""), check=False).stdout.strip()
        if not tip or not exists(landed["commit"]) or not is_ancestor(repo, landed["commit"], tip):
            findings.append(f"W07 landed: {ws.get('person_branch')} does not contain the landed commit")
    return (1 if findings else 0), {"findings": findings}


def cmd_land(a):
    head = git(a.repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip()
    if head != a.branch:
        return 5, {"kind": "not_landed", "reason": f"the main checkout is on {head or 'a detached HEAD'}, not {a.branch}"}
    r = git(a.repo, "merge", "--ff-only", a.commit, check=False)
    if r.returncode != 0:
        return 5, {"kind": "not_landed", "reason": "not a fast-forward of " + a.branch + ": " + (r.stderr.strip().splitlines() or ["git refused"])[-1]}
    return 0, {"kind": "fast_forward", "commit": out(a.repo, "rev-parse", "HEAD")}


def cmd_cleanup(a):
    root = os.path.realpath(a.root)
    listing = out(a.repo, "worktree", "list", "--porcelain").splitlines()
    paths = [l.split(" ", 1)[1] for l in listing if l.startswith("worktree ")]
    removed, kept = [], []
    for p in paths:
        rp = os.path.realpath(p)
        if os.path.commonpath([rp, root]) != root:
            continue
        if out(p, "status", "--porcelain"):
            kept.append(p); continue
        git(a.repo, "worktree", "remove", p)
        removed.append(p)
    git(a.repo, "worktree", "prune")
    if os.path.isdir(root) and not os.listdir(root):
        os.rmdir(root)
    return (1 if kept else 0), {"removed": removed, "kept": kept}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="worktrees.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start"); p.add_argument("repo"); p.add_argument("--slug", required=True)
    p.add_argument("--run-dir", required=True); p.add_argument("--root"); p.add_argument("--scope", nargs="*")
    p = sub.add_parser("node"); p.add_argument("repo"); p.add_argument("--slug", required=True); p.add_argument("--node", required=True)
    p.add_argument("--attempt", type=int, required=True); p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--upstream", nargs="*"); p.add_argument("--graph"); p.add_argument("--root")
    p = sub.add_parser("commit"); p.add_argument("worktree"); p.add_argument("--message", required=True)
    p = sub.add_parser("scope"); p.add_argument("worktree"); p.add_argument("--base", required=True); p.add_argument("--commit", required=True)
    p.add_argument("--writes", nargs="*"); p.add_argument("--graph"); p.add_argument("--node")
    p = sub.add_parser("integrate"); p.add_argument("repo"); p.add_argument("--slug", required=True); p.add_argument("--attempt", type=int, required=True)
    p.add_argument("--base", required=True); p.add_argument("--graph"); p.add_argument("--accepted", nargs="+", required=True); p.add_argument("--root")
    p = sub.add_parser("verify"); p.add_argument("run_dir"); p.add_argument("--repo")
    p = sub.add_parser("land"); p.add_argument("repo"); p.add_argument("--commit", required=True); p.add_argument("--branch", required=True)
    p = sub.add_parser("cleanup"); p.add_argument("repo"); p.add_argument("--root", required=True)
    a = ap.parse_args(argv)
    if getattr(a, "attempt", 1) < 1:
        ap.error("--attempt must be >= 1")
    try:
        code, payload = globals()["cmd_" + a.cmd](a)
    except Fail as e:
        code, payload = e.code, e.payload
    except (OSError, yaml.YAMLError, KeyError, TypeError) as e:
        code, payload = 2, {"error": f"{type(e).__name__}: {e}"}
    print(json.dumps(payload, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
