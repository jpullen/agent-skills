#!/usr/bin/env python3
"""worktrees.py — the git worktree machinery of a graph-prompt v3.6 run (D67-D70).

Every step here is deterministic, so it runs as a program, never as a subagent
(layer_3). The lead calls it; builders never do.

  start     REPO --slug S --run-dir D [--root DIR] [--scope P ...] [--exclude PATTERN ...]
            record the run base (HEAD), check the scope paths are clean, keep the
            run directory (and any --exclude pattern) out of every worktree, create
            the baseline worktree.
  exclude   REPO PATTERN ...
            add gitignore patterns for byproducts the gates create (caches, logs) to
            the repository's local exclude file, shared by every worktree (RF-61).
  node      REPO --slug S --node N --attempt K --from SHA [--upstream U=SHA ...] [--graph G] [--carry PREV]
            create (or switch) the node's worktree onto branch graph/S/N/aK at SHA,
            then merge the upstream commits in topological order (ties by node id).
            Attempt 1: --from the run base. A retry: --from the previous attempt's
            commit, no upstreams. A rebuild after an upstream was re-accepted:
            --from the run base, the upstreams' newest commits, and --carry the
            node's previous commit, merged last. `upstream_base` in the output is
            the commit before the carry: the node's scope base (RF-67).
  commit    WORKTREE --message M [--author "Name <email>"]
            stage everything in the worktree and commit it; one commit per attempt.
            With --author, refuse (exit 3) unless git's effective identity is that
            author: a container restart can reset it (RF-74).
  scope     WORKTREE --base B --commit C (--writes P ... | --graph G --node N)
            list the paths changed between B and C and those outside the node's
            writes. B is the node's scope base: attempt 1's base, or the base of an
            attempt rebuilt on re-accepted upstreams (RF-62), so a retry that undoes
            an earlier attempt's out-of-scope write is not itself out of scope.
  integrate REPO --slug S --attempt K --base B0 --graph G --accepted N=SHA ...
            build graph/S/integration/aK from B0 by merging every accepted node's
            newest commit in topological order; confirm each is an ancestor.
  verify    RUN_DIR --repo REPO
            check every row's workspace against git: commits exist, base is an
            ancestor, branch tip and changed list agree, integration converges.
  history   REPO --base B --commit C [--exec CMD]
            list every commit a push of C would publish beyond B, with its author
            and changed paths. With --exec, check each commit out in a scratch
            worktree and run CMD there (shell; the tree path is appended); exit 1
            if CMD fails on any commit (RF-73: gates read the tree, a push
            publishes the history).
  land      REPO --commit C --branch PB [--squash --base B --message M [--author A]]
            fast-forward the person's branch to C; anything but a fast-forward is
            not landed. With --squash, land one new commit on B that carries C's
            tree, so no attempt's history is published.
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


def add_excludes(repo, patterns):
    exclude = os.path.join(out(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"), "info", "exclude")
    os.makedirs(os.path.dirname(exclude), exist_ok=True)
    existing = open(exclude, encoding="utf-8").read().splitlines() if os.path.exists(exclude) else []
    added = [p for p in patterns if p not in existing]
    with open(exclude, "a", encoding="utf-8") as fh:
        for p in added:
            fh.write(p + "\n")
    return exclude, added


def cmd_exclude(a):
    path, added = add_excludes(a.repo, a.patterns)
    return 0, {"exclude_file": path, "added": added}


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
            add_excludes(top, [f"/{rel.replace(os.sep, '/')}/"])
    excluded = add_excludes(top, a.exclude)[1] if a.exclude else []
    root = os.path.abspath(a.root) if a.root else default_root(top, a.slug)
    if os.path.relpath(root, run_dir).split(os.sep)[0] != "..":
        raise Fail(3, {"error": "the worktree root is inside the run directory", "root": root})
    if os.path.exists(root):
        raise Fail(3, {"error": "the worktree root already exists; a run creates its own", "root": root})
    os.makedirs(os.path.dirname(root), exist_ok=True)
    git(top, "worktree", "add", "--detach", os.path.join(root, "baseline"), base)
    return 0, {"kind": "worktree", "repo": top, "base": base, "person_branch": branch.stdout.strip(),
               "root": root, "baseline": os.path.join(root, "baseline"), "excluded": excluded}


def cmd_node(a):
    root = os.path.abspath(a.root) if a.root else default_root(a.repo, a.slug)
    wt = os.path.join(root, a.node)
    branch = f"graph/{a.slug}/{a.node}/a{a.attempt}"
    upstream = ordered(parse_pairs(a.upstream), a.graph)  # validate before any side effect (RF-58)
    start = out(a.repo, "rev-parse", "--verify", a.from_ + "^{commit}")
    carry = out(a.repo, "rev-parse", "--verify", a.carry + "^{commit}") if a.carry else None
    if os.path.isdir(wt):
        if out(wt, "status", "--porcelain"):
            raise Fail(3, {"error": "the node's worktree has uncommitted changes", "worktree": wt})
        git(wt, "switch", "-c", branch, start)
    else:
        git(a.repo, "worktree", "add", "-b", branch, wt, start)
    merge_all(wt, upstream, f"graph({a.slug}): {a.node} a{a.attempt} base")
    upstream_base = out(wt, "rev-parse", "HEAD")
    if carry:
        merge_all(wt, [(f"{a.node} previous attempt", carry)], f"graph({a.slug}): {a.node} a{a.attempt} carry")
    return 0, {"worktree": wt, "branch": branch, "base": out(wt, "rev-parse", "HEAD"), "upstream_base": upstream_base}


def check_author(repo, author):
    if not author:
        return
    actual = f"{git(repo, 'config', 'user.name', check=False).stdout.strip()} <{git(repo, 'config', 'user.email', check=False).stdout.strip()}>"
    if actual != author:
        raise Fail(3, {"error": "git identity is not the run's author", "expected": author, "actual": actual})


def cmd_commit(a):
    check_author(a.worktree, a.author)
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
    accepted = ordered(parse_pairs(a.accepted), a.graph)  # validate before any side effect (RF-58)
    if os.path.isdir(wt):
        if out(wt, "status", "--porcelain"):
            raise Fail(3, {"error": "the integration worktree has uncommitted changes", "worktree": wt})
        git(wt, "switch", "-c", branch, a.base)
    else:
        git(a.repo, "worktree", "add", "-b", branch, wt, a.base)
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
    prog = y("progress")  # run-record files carry no top-level wrapper key (RF-63)
    ws = prog.get("workspace") or {}
    findings = []
    if ws.get("kind") != "worktree":
        return 0, {"findings": [], "note": "progress.workspace.kind is not worktree; nothing to verify"}
    repo = a.repo or ws.get("repo")
    exists = lambda sha: git(repo, "cat-file", "-e", sha + "^{commit}", check=False).returncode == 0
    newest, attempts = {}, {}
    for r in sorted(rows, key=lambda r: r["attempt"]):
        w = r.get("workspace")
        if not w:
            continue
        s = r["subject"]
        who = f"{s.get('node') or s.get('item') or s['kind']}#{r['attempt']}"
        if not exists(w["commit"]) or not exists(w["base"]):
            findings.append(f"W01 {who}: commit or base not in the repository"); continue
        scope_base = w.get("scope_base", w["base"])
        if not exists(scope_base):
            findings.append(f"W02 {who}: scope_base is not in the repository"); continue  # RF-66: no diff against a missing commit
        if not is_ancestor(repo, w["base"], w["commit"]) or not is_ancestor(repo, scope_base, w["base"]):
            findings.append(f"W02 {who}: base is not an ancestor of commit, or scope_base is not an ancestor of base")
        tip = git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/" + w["branch"], check=False).stdout.strip()
        if tip != w["commit"]:
            findings.append(f"W03 {who}: branch {w['branch']} tip is {tip[:12] or 'missing'}, not the recorded commit")
        diff = set(out(repo, "diff", "--name-only", scope_base, w["commit"]).splitlines())
        if diff != set(w["changed"]):
            findings.append(f"W04 {who}: changed list differs from git diff (git has {sorted(diff ^ set(w['changed']))} different)")
        if s["kind"] == "node":
            prev = attempts.get((s["node"], r["attempt"] - 1))
            if prev and exists(prev) and not is_ancestor(repo, prev, w["base"]):
                findings.append(f"W08 {who}: the previous attempt's commit is not contained in this attempt's base")
            attempts[(s["node"], r["attempt"])] = w["commit"]
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
    if landed.get("kind") == "squashed" and exists(landed["commit"]):
        parents = out(repo, "rev-list", "--parents", "-n", "1", landed["commit"]).split()[1:]
        same_tree = integ and exists(integ[1]) and out(repo, "rev-parse", landed["commit"] + "^{tree}") == out(repo, "rev-parse", integ[1] + "^{tree}")
        if parents != [ws.get("base")] or not same_tree:
            findings.append("W09 landed: the squashed commit is not one commit on the run base carrying the newest integration tree")
    if ws.get("author") and exists(ws.get("base", "0" * 40)):
        tips = sorted({sha for sha in attempts.values() if exists(sha)} | ({integ[1]} if integ and exists(integ[1]) else set()))
        run_commits = out(repo, "rev-list", *tips, "--not", ws["base"]).splitlines() if tips else []
        for sha in run_commits:
            who = out(repo, "log", "-1", "--format=%an <%ae>", sha)
            if who != ws["author"]:
                findings.append(f"W10 {sha[:12]}: commit author {who} is not the run's author {ws['author']}")
    if landed.get("kind") in ("fast_forward", "squashed"):
        tip = git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/" + ws.get("person_branch", ""), check=False).stdout.strip()
        if not tip or not exists(landed["commit"]) or not is_ancestor(repo, landed["commit"], tip):
            findings.append(f"W07 landed: {ws.get('person_branch')} does not contain the landed commit")
    return (1 if findings else 0), {"findings": findings}


def cmd_history(a):
    commits = out(a.repo, "rev-list", "--reverse", f"{a.base}..{a.commit}").splitlines()
    scratch = None
    if a.exec_:
        scratch = os.path.join(out(a.repo, "rev-parse", "--path-format=absolute", "--git-common-dir"), "graph-worktrees", f"history-{os.getpid()}")
        git(a.repo, "worktree", "add", "--detach", scratch, a.base)
    rows, failed = [], []
    try:
        for c in commits:
            row = {"commit": c, "author": out(a.repo, "log", "-1", "--format=%an <%ae>", c), "subject": out(a.repo, "log", "-1", "--format=%s", c),
                   "paths": out(a.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", "--first-parent", c).splitlines()}
            if scratch:
                git(scratch, "checkout", "-q", "--detach", c)
                r = subprocess.run(f"{a.exec_} {scratch}", shell=True, capture_output=True, text=True, cwd=scratch)
                row["exit"] = r.returncode
                if r.returncode != 0:
                    failed.append(c)
            rows.append(row)
    finally:
        if scratch:
            git(a.repo, "worktree", "remove", "--force", scratch, check=False)  # the scratch tree is this command's own
    return (1 if failed else 0), {"count": len(rows), "failed": failed, "commits": rows}


def cmd_land(a):
    head = git(a.repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip()
    if head != a.branch:
        return 5, {"kind": "not_landed", "reason": f"the main checkout is on {head or 'a detached HEAD'}, not {a.branch}"}
    if a.squash:
        if not a.base or not a.message:
            raise Fail(2, {"error": "--squash needs --base and --message"})
        check_author(a.repo, a.author)
        if out(a.repo, "rev-parse", "HEAD") != out(a.repo, "rev-parse", a.base + "^{commit}"):
            return 5, {"kind": "not_landed", "reason": f"{a.branch} is no longer at the run base; a squash onto it would not be a fast-forward"}
        new = out(a.repo, "commit-tree", a.commit + "^{tree}", "-p", a.base, "-m", a.message)
        r = git(a.repo, "merge", "--ff-only", new, check=False)
        if r.returncode != 0:
            return 5, {"kind": "not_landed", "reason": "the squashed commit could not be checked out: " + (r.stderr.strip().splitlines() or ["git refused"])[-1]}
        return 0, {"kind": "squashed", "commit": new}
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
    p.add_argument("--run-dir", required=True); p.add_argument("--root"); p.add_argument("--scope", nargs="*", action="extend"); p.add_argument("--exclude", nargs="*", action="extend")
    p = sub.add_parser("exclude"); p.add_argument("repo"); p.add_argument("patterns", nargs="+")
    p = sub.add_parser("node"); p.add_argument("repo"); p.add_argument("--slug", required=True); p.add_argument("--node", required=True)
    p.add_argument("--attempt", type=int, required=True); p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--upstream", nargs="*", action="extend"); p.add_argument("--graph"); p.add_argument("--root"); p.add_argument("--carry")
    p = sub.add_parser("commit"); p.add_argument("worktree"); p.add_argument("--message", required=True); p.add_argument("--author")
    p = sub.add_parser("history"); p.add_argument("repo"); p.add_argument("--base", required=True); p.add_argument("--commit", required=True); p.add_argument("--exec", dest="exec_")
    p = sub.add_parser("scope"); p.add_argument("worktree"); p.add_argument("--base", required=True); p.add_argument("--commit", required=True)
    p.add_argument("--writes", nargs="*", action="extend"); p.add_argument("--graph"); p.add_argument("--node")
    p = sub.add_parser("integrate"); p.add_argument("repo"); p.add_argument("--slug", required=True); p.add_argument("--attempt", type=int, required=True)
    p.add_argument("--base", required=True); p.add_argument("--graph"); p.add_argument("--accepted", nargs="+", action="extend", required=True); p.add_argument("--root")
    p = sub.add_parser("verify"); p.add_argument("run_dir"); p.add_argument("--repo")
    p = sub.add_parser("land"); p.add_argument("repo"); p.add_argument("--commit", required=True); p.add_argument("--branch", required=True)
    p.add_argument("--squash", action="store_true"); p.add_argument("--base"); p.add_argument("--message"); p.add_argument("--author")
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
