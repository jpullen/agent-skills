"""Synthetic scenario engine: a scripted lead that runs any graph shape with injected faults through the real kit.

A scenario is a plain dict (see catalog.py). The engine builds a throwaway repository, follows prompt v3.6's order —
start, baseline, one branch and one commit per attempt, scope diff and gate, record after every terminal state,
integration, both audits, history gate, landing, cleanup — calling worktrees.py for every git step, and then applies
the scenario's record corruptions to copies of the final record. It returns a fingerprint: a JSON-able dict that holds
no path, time or random value, so two runs of one scenario can be compared field by field.

Determinism: every git process gets fixed author and committer dates and no global or system git config, so commit
ids are a function of the scenario alone and are part of the fingerprint.

What this cannot show is a model's behaviour: builders here are functions, and the lead is this file.
"""
import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent
RECORD = SCRIPTS.parent.parent / "graph-record" / "scripts"
WT = SCRIPTS / "worktrees.py"
SLUG = "synth"
AUTHOR = "Synth Lead <lead@synth.invalid>"
WRONG_AUTHOR = ("Claude", "noreply@anthropic.com")
MODELS = "tier-low,tier-mid,tier-high"
DATE = "2026-01-01T00:00:00+0000"
ENV = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
       "PYTHONDONTWRITEBYTECODE": "1", "GIT_AUTHOR_DATE": DATE, "GIT_COMMITTER_DATE": DATE,
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C"}
ABSENCE = "! grep -rqs SECRET --exclude-dir=.git . #"   # history --exec appends the tree path; '#' drops it


def sh(cwd, *args, check=True):
    r = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, env=ENV)
    if check and r.returncode != 0:
        raise RuntimeError(f"{args[:3]}: exit {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def topo(nodes):
    order, done = [], set()
    while len(order) < len(nodes):
        ready = sorted(n for n, ups in nodes.items() if n not in done and set(ups) <= done)
        order.append(ready[0]); done.add(ready[0])
    return order


def descendants(nodes, x):
    out, frontier = set(), {x}
    while frontier:
        nxt = {n for n, ups in nodes.items() if set(ups) & frontier} - out
        out |= nxt; frontier = nxt
    return out


def ancestors(nodes, x):
    out, frontier = set(), set(nodes[x])
    while frontier:
        out |= frontier
        frontier = {u for f in frontier for u in nodes[f]} - out
    return out


class Scenario:
    def __init__(self, spec, tmp):
        self.spec = spec
        self.nodes = spec["nodes"]
        self.order = topo(self.nodes)
        self.repo = pathlib.Path(tmp) / "repo"
        self.run_dir = self.repo / ".graph" / SLUG
        self.code = self.run_dir / "code"
        self.calls = []
        self.fp = {"id": spec["id"], "calls": self.calls, "attempts": {n: [] for n in self.order}, "integration": [], "probes": {}}
        self.attempts, self.ws, self.accepted, self.scope_base = {}, {}, {}, {}
        self.consumed = 0
        self.faults = {f["node"]: f for f in spec["faults"]}
        self.plan = {n: self._plan(n) for n in self.order}
        self.integration = None
        self._v = {}

    # -- helpers ---------------------------------------------------------------------------
    def wt(self, *args):
        r = sh(self.repo, sys.executable, WT, *args, check=False)
        self.calls.append([str(args[0]), r.returncode])
        try:
            return r.returncode, json.loads(r.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"worktrees.py {args[0]}: no JSON (exit {r.returncode})\n{r.stdout}\n{r.stderr}")

    def v(self, n):
        # per instance: a cache keyed by object id leaked values between scenarios in one worker process
        if n not in self._v:
            self._v[n] = hashlib.sha256((n + "|" + "|".join(self.v(u) for u in sorted(self.nodes[n]))).encode()).hexdigest()[:16]
        return self._v[n]

    def tier(self, n):
        """X25: the tier rule's lines are a function of the node; reading three or more upstreams moves it up one tier."""
        lines = ["reads_three_or_more_upstream"] if len(self.nodes[n]) >= 3 else []
        return MODELS.split(",")[len(lines)], lines

    def _plan(self, n):
        kind = self.faults.get(n, {}).get("kind")
        return {"wrong": ["wrong", "good"], "scope": ["scope", "undo"], "empty": ["empty", "good"], "partial": ["partial"],
                "secret": ["secret", "good"], "conflict": ["conflict", "undo"], "upstream_bad": ["loose_wrong", "good"]}.get(kind, ["good"])

    # -- builders: plain functions of the tree ---------------------------------------------
    def build(self, n, behavior, tree):
        out = tree / "out"; out.mkdir(exist_ok=True)
        own = out / f"{n}.txt"
        good = lambda: own.write_text(self.v(n) + "\n")
        if behavior in ("good", "partial"):
            good()
        elif behavior == "wrong":
            own.write_text(("0" if self.v(n)[0] != "0" else "1") + self.v(n)[1:] + "\n")
        elif behavior == "scope":
            good(); (tree / "stray").mkdir(exist_ok=True); (tree / "stray" / f"{n}.txt").write_text("stray\n")
        elif behavior == "conflict":
            good(); (out / f"{self.faults[n]['sibling']}.txt").write_text("stray\n")
        elif behavior == "undo":
            keep = {f"{x}.txt" for x in ancestors(self.nodes, n) | {n}}
            for p in out.iterdir():
                if p.name not in keep and not p.name.startswith("."):
                    p.unlink()
            shutil.rmtree(tree / "stray", ignore_errors=True)
            good()
        elif behavior == "secret":
            own.write_text(self.v(n) + "\nSECRET leak\n")
        elif behavior == "loose_wrong":
            own.write_text(self.v(n)[::-1] + "\n" if self.v(n)[::-1] != self.v(n) else "f" * 16 + "\n")
        elif behavior == "late":
            own.write_text(self.v(n) + "\n# reviewed\n")
        elif behavior in ("empty", "nothing"):
            pass
        else:
            raise ValueError(behavior)

    # -- setup -----------------------------------------------------------------------------
    def setup(self):
        (self.repo / "out").mkdir(parents=True)
        sh(self.repo, "git", "init", "-q", "-b", "main")
        name, email = AUTHOR[:-1].split(" <")
        sh(self.repo, "git", "config", "user.name", name); sh(self.repo, "git", "config", "user.email", email)
        (self.repo / "SPEC.md").write_text("# synthetic\n\nEach node writes out/<node>.txt holding v(node). No file holds the leak token that accept.py names.\n")
        (self.repo / "out" / ".keep").write_text("")
        sh(self.repo, "git", "add", "-A"); sh(self.repo, "git", "commit", "-q", "-m", "synthetic: spec")
        self.code.mkdir(parents=True)
        for f in ("gate.py", "accept.py"):
            shutil.copy(HERE / f, self.code / f)
        loose = [x for x, f in self.faults.items() if f["kind"] == "upstream_bad"]
        (self.code / "spec.json").write_text(json.dumps({"nodes": self.nodes, "loose": loose, "byproduct": bool(self.spec.get("flags", {}).get("byproduct"))}, sort_keys=True))
        if self.spec.get("flags", {}).get("dirty_start"):
            (self.repo / "out" / "person.txt").write_text("uncommitted\n")

    def start(self):
        code, s = self.wt("start", self.repo, "--slug", SLUG, "--run-dir", self.run_dir, "--scope", "out", "stray")
        if code != 0:
            self.fp["outcome"] = f"blocked_at_start: {s.get('error')}"
            return False
        self.base, self.root, self.startinfo = s["base"], pathlib.Path(s["root"]), s
        self.red = {}
        for n in self.order:
            r = sh(s["baseline"], sys.executable, self.code / "gate.py", n, check=False)
            assert r.returncode == 1, f"{n} gate green at baseline"
            self.red[n] = r.stdout.strip()
        r = sh(self.repo, sys.executable, self.code / "accept.py", s["baseline"], check=False)
        assert r.returncode == 1
        self.red_accept = dict(l.split() for l in r.stdout.split("\n") if l)
        # <worktrees> Start: every path git status lists in the baseline worktree after baseline is a gate byproduct
        self.byproducts = [l[3:] for l in sh(s["baseline"], "git", "status", "--porcelain").stdout.splitlines()]
        if self.byproducts:
            code, _ = self.wt("exclude", self.repo, *self.byproducts)
            assert code == 0
        self.fp["byproducts"] = self.byproducts
        return True

    # -- record ----------------------------------------------------------------------------
    def node_proto(self, n, k):
        return {"subject": {"kind": "node", "node": n, "check": f"{n}-gate"}, "attempt": k, "requirement": f"out/{n}.txt holds v({n}); changes inside writes",
                "type": "exec", "isolation": {"kind": "not_run", "reason": "not dispatched"},
                "fails_when": "gate.py exits non-zero or the scope diff lists a path outside writes",
                "red_evidence": {"kind": "assertion_failure", "test_path": str(self.code / "gate.py"), "summary": f"baseline: {self.red[n]}"},
                "verdict": "unresolved", "evidence": {"kind": "not_run", "reason": "not dispatched"}}

    def write_record(self):
        single = len(self.order) == 1
        self.graph = {"nodes": [{
            "id": n, "purpose": f"synthetic node {n}", "does": [{"imperative": f"write v({n})", "produces": "value"}], "shape": ["value"],
            "split_reason": {"kind": "single_node"} if single else {"kind": "context", "what": "synthetic node"},
            "reads": {"sources": True, "upstream": [{"node": u, "sections": ["value"]} for u in sorted(self.nodes[n])]},
            "writes": [f"out/{n}.txt"], "needs": [], "kind": "judgment",
            "checks": [{"id": f"{n}-gate", "type": "exec", "content": f"gate.py {n} in the node's worktree, plus the scope diff",
                        "fails_when": "gate.py exits non-zero or the scope diff lists a path outside writes", "exec_available": "yes"}],
            "rules": {"kind": "judgment"}, "model": {"tier": self.tier(n)[0], "tier_rule": self.tier(n)[1], "escalations": 0}} for n in self.order]}
        self.rules = {"rules": [{"id": f"r-{n}", "spec": "SPEC.md", "rule": f"out/{n}.txt holds v({n})", "section": "", "quote": "Each node writes out/<node>.txt holding v(node).",
                                 "concerns": ["deliverable"]} for n in self.order]
                      + [{"id": "r-secret", "spec": "SPEC.md", "rule": "no file holds SECRET", "section": "", "quote": "No file holds the leak token that accept.py names.", "concerns": ["deliverable"]}]}
        first = self.order[0]
        self.framing = {"problem": f"synthetic scenario {self.spec['id']}", "goals": ["every node's value holds on the merged deliverable"],
                        "constraints": ["autonomous mode"], "assumptions": [], "unknowns": [],
                        "risks": [{"id": "r1", "text": "a builder writes outside its writes", "guarded_by": {"kind": "gate", "node": first, "check": f"{first}-gate"}}],
                        "inputs": {"task": "synthetic", "output": "out/", "sources": ["SPEC.md"], "scope": ["out/", "stray/"], "mode": "autonomous",
                                   "models": MODELS.split(","), "priorities": [], "author": AUTHOR}}
        self.rows = [self.node_proto(n, 1) for n in self.order]
        for k, ex in (("k1", [f"r-{n}" for n in self.order]), ("k2", ["r-secret"])):
            self.rows.append({"subject": {"kind": "acceptance", "item": k}, "attempt": 1, "requirement": f"accept.py item {k}", "type": "exec",
                              "isolation": {"kind": "not_run", "reason": "integration not run"}, "fails_when": f"accept.py prints '{k} fail'",
                              "red_evidence": {"kind": "checks_baseline", "summary": f"{k} {self.red_accept[k]} on the baseline worktree"},
                              "verdict": "unresolved", "evidence": {"kind": "not_run", "reason": "integration not run"}, "exercises": ex})
        self.progress = {
            "enforcement": {"kind": "instruction_only"},
            "graph": {k: [] for k in ("accepted", "running", "failed", "blocked", "dissent", "escalated", "not_started")},
            "outputs": [], "decisions": [{"kind": "approval_default", "reason": "autonomous mode"},
                                         {"kind": "other", "reason": f"gate byproducts in the baseline worktree after baseline, excluded before any node ran: {self.byproducts or 'none'}"}],
            "assumptions": [], "open_issues": [], "unchecked_rules": [], "subagents": [],
            "audits": {"wellformed": {"exit_code": 0, "isolation": "na_code"},
                       "evidence": {"isolation": {"kind": "not_run", "reason": "not reached"}, "rows": 0, "miscited": 0, "unfound": 0, "verdict": "not_run", "notes": []}},
            "hypotheses": [], "usage": {"limit": 500, "unit": "node_runs", "consumed": 0, "lead_tokens": None},
            "next_action": {"kind": "node", "node": first},
            "workspace": {**{k: self.startinfo[k] for k in ("kind", "repo", "base", "person_branch", "root")}, "author": AUTHOR}}
        self.progress["graph"]["not_started"] = list(self.order)
        self.lessons = {"entries": []}
        self.save()

    def save(self, run_dir=None):
        d = run_dir or self.run_dir
        for name in ("graph", "rules", "framing", "progress", "lessons"):
            (d / f"{name}.yaml").write_text(yaml.safe_dump(getattr(self, name), sort_keys=False, width=200))
        (d / "checks.yaml").write_text(yaml.safe_dump({"rows": self.rows}, sort_keys=False, width=200))

    def decide(self, reason, node=None, phase=None):
        d = {"kind": "other", "reason": reason}
        if node: d["node"] = node
        if phase: d["phase"] = phase
        self.progress["decisions"].append(d)

    def move(self, n, to):
        g = self.progress["graph"]
        for lst in g.values():
            if n in lst: lst.remove(n)
        g[to].append(n)

    # -- one attempt -----------------------------------------------------------------------
    def attempt(self, n, behavior, mode):
        """mode: first | retry | rebuild. Returns (verdict, gate message)."""
        k = self.attempts.get(n, 0) + 1
        prev = self.ws.get((n, k - 1))
        args = ["node", self.repo, "--slug", SLUG, "--node", n, "--attempt", k, "--graph", self.run_dir / "graph.yaml"]
        if mode in ("first", "rebuild"):
            args += ["--from", self.base]
            for u in sorted(self.nodes[n]):
                args += ["--upstream", f"{u}={self.accepted[u]}"]
            if mode == "rebuild":
                args += ["--carry", prev["commit"]]
        else:
            args += ["--from", prev["commit"]]
        code, made = self.wt(*args)
        assert code == 0, made
        tree, base = pathlib.Path(made["worktree"]), made["base"]
        if mode in ("first", "rebuild"):
            self.scope_base[n] = made["upstream_base"]
        cause = {"first": None, "retry": "builder_error", "rebuild": "upstream_field"}[mode]
        if k > 1:
            self.progress["hypotheses"].append({"node": n, "before_attempt": k, "cause": cause, "disconfirmation": "the attempt's gate fails on the same section"})
        self.build(n, behavior, tree)
        self.consumed += 1
        self.progress["subagents"].append({"id": f"synth-{n}-{k}", "role": "builder", "node": n, "tier": self.tier(n)[0]})
        if self.faults.get(n, {}).get("identity") and k == 1:
            sh(self.repo, "git", "config", "user.name", WRONG_AUTHOR[0]); sh(self.repo, "git", "config", "user.email", WRONG_AUTHOR[1])
        code, c = self.wt("commit", tree, "--message", f"graph({SLUG}): {n} a{k}", "--author", AUTHOR)
        if code == 3:
            name, email = AUTHOR[:-1].split(" <")
            sh(self.repo, "git", "config", "user.name", name); sh(self.repo, "git", "config", "user.email", email)
            self.decide("commit refused under a reset git identity; set to the given author and committed again", node=n)
            code, c = self.wt("commit", tree, "--message", f"graph({SLUG}): {n} a{k}", "--author", AUTHOR)
        assert code in (0, 4), c
        commit = c["commit"] if code == 0 else base
        sb = self.scope_base[n]
        scode, scope = self.wt("scope", tree, "--base", sb, "--commit", commit, "--graph", self.run_dir / "graph.yaml", "--node", n)
        gate = sh(tree, sys.executable, self.code / "gate.py", n, check=False)
        actual = gate.returncode or scode
        verdict = "pass" if actual == 0 else "fail"
        msg = gate.stdout.strip()
        ws = {"branch": made["branch"], "base": base, "scope_base": sb, "commit": commit, "changed": scope["changed"]}
        row = self.node_proto(n, k)
        row.update(isolation={"kind": "na_exec"}, verdict=verdict, workspace=ws, evidence={
            "kind": "exec", "expected_exit": 0, "actual_exit": actual,
            "command": f"cd {tree} && {sys.executable} {self.code / 'gate.py'} {n} && {sys.executable} {WT} scope {tree} --base {sb} --commit {commit} --graph {self.run_dir / 'graph.yaml'} --node {n}",
            "output": f"{msg}; scope outside {scope['outside']}"})
        if k == 1:
            self.rows[next(i for i, r in enumerate(self.rows) if r["subject"].get("node") == n)] = row
        else:
            self.rows.insert(max(i for i, r in enumerate(self.rows) if r["subject"].get("node") == n) + 1, row)
        self.attempts[n], self.ws[(n, k)] = k, ws
        if verdict == "pass":
            self.accepted[n] = commit
            self.move(n, "accepted")
            if f"out/{n}.txt" not in self.progress["outputs"]:
                self.progress["outputs"].append(f"out/{n}.txt")
        else:
            self.accepted.pop(n, None)
            self.move(n, "running")
        self.progress["usage"]["consumed"] = self.consumed
        self.progress["next_action"] = {"kind": "node", "node": n}
        self.save()
        self.fp["attempts"][n].append({"k": k, "mode": mode, "behavior": behavior, "verdict": verdict, "gate": msg,
                                       "outside": scope["outside"], "changed": scope["changed"], "commit": commit})
        return verdict, msg

    def run_node(self, n, mode="first"):
        for _ in range(8):
            behavior = self.plan[n].pop(0) if self.plan[n] else "good"
            verdict, msg = self.attempt(n, behavior, mode)
            if verdict == "pass":
                return
            if msg.startswith("UPSTREAM "):
                u = msg.split()[1]
                self.decide(f"{n} failed on {u}'s value: cause (b); {u} reopens", node=n)
                self.move(u, "running"); self.accepted.pop(u, None)
                self.run_node(u, "retry")
                self.rebuild_descendants(u, skip={n})
                self.plan[n].insert(0, "nothing")
                mode = "rebuild"
            else:
                mode = "retry"
        raise RuntimeError(f"{n}: no pass in 8 attempts")

    def rebuild_descendants(self, u, skip=()):
        for d in self.order:
            if d in descendants(self.nodes, u) and d not in skip and d in self.accepted:
                self.run_node_rebuild(d)

    def run_node_rebuild(self, d):
        verdict, msg = self.attempt(d, "nothing", "rebuild")
        assert verdict == "pass", (d, msg)

    # -- convergence -----------------------------------------------------------------------
    def integrate(self):
        k = (self.integration or {}).get("attempt", 0) + 1
        args = ["integrate", self.repo, "--slug", SLUG, "--attempt", k, "--base", self.base, "--graph", self.run_dir / "graph.yaml"]
        for n in sorted(self.accepted, reverse=True):
            args += ["--accepted", f"{n}={self.accepted[n]}"]
        code, ig = self.wt(*args)
        assert code == 0, ig
        cmd = f"{sys.executable} {self.code / 'accept.py'} {ig['worktree']}"
        r = sh(self.repo, sys.executable, self.code / "accept.py", ig["worktree"], check=False)
        (self.run_dir / "integration.out").write_text(r.stdout)
        self.consumed += 1
        lines = dict(l.split() for l in r.stdout.split("\n") if l)
        ws = {"branch": ig["branch"], "base": self.base, "scope_base": self.base, "commit": ig["commit"], "changed": ig["changed"]}
        fresh = []
        for item in ("k1", "k2"):
            row = copy.deepcopy(next(x for x in self.rows if x["subject"].get("item") == item))
            row.update(attempt=k, isolation={"kind": "na_exec"}, verdict=lines[item], workspace=ws,
                       evidence={"kind": "exec", "command": cmd, "expected_exit": 0, "actual_exit": r.returncode, "output": f"{item} {lines[item]}"})
            fresh.append(row)
        fresh.append({"subject": {"kind": "integration"}, "attempt": k, "requirement": "every acceptance item passes", "type": "exec",
                      "isolation": {"kind": "na_exec"}, "fails_when": "accept.py exits non-zero",
                      "red_evidence": {"kind": "checks_baseline", "summary": "k1 fails on the baseline worktree"},
                      "verdict": "pass" if r.returncode == 0 else "fail", "workspace": ws,
                      "evidence": {"kind": "exec", "command": cmd, "expected_exit": 0, "actual_exit": r.returncode, "output": " / ".join(f"{i} {v}" for i, v in lines.items())}})
        if k == 1:
            self.rows = [x for x in self.rows if x["subject"]["kind"] == "node"] + fresh
        else:
            self.rows += fresh
            self.progress["hypotheses"] += [{"node": who, "before_attempt": k, "cause": "upstream_field", "disconfirmation": "the item fails again"} for who in ("k1", "k2", "integration")]
        self.integration = {"attempt": k, **ig}
        self.progress["workspace"]["integration_branch"] = ig["branch"]
        self.progress["usage"]["consumed"] = self.consumed
        self.progress["next_action"] = {"kind": "delivery"}
        self.save()
        self.fp["integration"].append({"attempt": k, "order": ig["order"], "commit": ig["commit"], "accept": lines})

    # -- audits ----------------------------------------------------------------------------
    def validate(self, run_dir=None):
        r = sh(self.repo, sys.executable, RECORD / "validate.py", run_dir or self.run_dir, "--models", MODELS, "--all", check=False)
        codes = sorted({l.split()[0] for l in r.stdout.splitlines() if l and not l.startswith(("OK", "..."))})
        return r.returncode, codes

    def verify(self, run_dir=None):
        code, v = self.wt("verify", run_dir or self.run_dir)
        return code, sorted({f.split()[0] for f in v.get("findings", [])})

    def evidence_audit(self):
        newest = {}
        for r in self.rows:
            if r["verdict"] == "pass" and r["type"] == "exec":
                s = r["subject"]; key = (s["kind"], s.get("node"), s.get("item"))
                if key not in newest or r["attempt"] > newest[key]["attempt"]:
                    newest[key] = r
        miscited = unfound = 0
        for r in newest.values():
            ev = r["evidence"]
            run = subprocess.run(ev["command"], shell=True, capture_output=True, text=True, cwd="/", env=ENV)
            if run.returncode == 127 or "No such file" in run.stderr:
                unfound += 1
            elif run.returncode != ev["actual_exit"]:
                miscited += 1
        self.consumed += 1
        self.progress["subagents"].append({"id": "synth-audit", "role": "evidence_audit", "phase": "audit", "tier": "tier-mid"})
        rows = len(newest)
        self.progress["audits"]["evidence"] = {"isolation": {"kind": "fresh_subagent", "subagent": "synth-audit"}, "rows": rows, "miscited": miscited, "unfound": unfound,
                                               "verdict": "pass" if rows == 0 or (miscited + unfound) / rows <= 0.10 else "fail", "notes": []}
        self.progress["usage"]["consumed"] = self.consumed
        return [rows, miscited, unfound]

    # -- the run ---------------------------------------------------------------------------
    def run(self):
        self.setup()
        if not self.start():
            return self.fp
        self.write_record()
        for n in self.order:
            if n not in self.accepted:
                self.run_node(n)
        for x, f in sorted(self.faults.items()):
            if f["kind"] == "conflict":
                self.conflict_probes(x, f["sibling"])
        self.integrate()
        late = [x for x, f in sorted(self.faults.items()) if f["kind"] == "late"]
        for x in late:
            self.decide(f"a correction to {x} after integration", node=x)
            self.move(x, "running"); self.accepted.pop(x)
            verdict, _ = self.attempt(x, "late", "retry")
            assert verdict == "pass"
            self.rebuild_descendants(x)
            self.fp["probes"]["stale_integration_verify"] = self.verify()
            self.integrate()
        a = self.fp["audits"] = {}
        a["validate_audit1"], _ = self.validate()
        a["verify_audit1"] = self.verify()
        a["evidence"] = self.evidence_audit()
        self.save()
        code, h = self.wt("history", self.repo, "--base", self.base, "--commit", self.integration["commit"], "--exec", ABSENCE, "--forbid", "SECRET")
        failed = [i for i, row in enumerate(h["commits"]) if row["commit"] in h["failed"]]
        self.fp["history"] = {"count": h["count"], "failed_index": failed}
        squash = bool(h["failed"]) or self.spec["delivery"] == "squash"
        self.decide("history disposition: " + ("squashed" if squash else "gated"), phase="delivery")
        if self.spec["delivery"] == "moved":
            (self.repo / "PERSON.md").write_text("person's change\n")
            sh(self.repo, "git", "add", "PERSON.md")
            sh(self.repo, "git", "-c", "user.name=Person", "-c", "user.email=person@synth.invalid", "commit", "-q", "-m", "person: change during the run")
        args = ["land", self.repo, "--commit", self.integration["commit"], "--branch", "main"]
        if squash:
            args += ["--squash", "--base", self.base, "--message", f"graph({SLUG}): deliver", "--author", AUTHOR]
        _, landed = self.wt(*args)
        self.progress["workspace"]["landed"] = landed
        self.lessons = {"entries": [{"node": n, "evidence": f"gate passed at attempt {k}", "tier": self.tier(n)[0], "tier_rule": self.tier(n)[1], "attempt": k,
                                     "confirmed_in": 1, "promoted": False} for n, k in self.attempts.items()]}
        self.save()
        self.fp["landed"] = {"kind": landed["kind"], "commit": landed.get("commit")}
        a["validate_delivery"], a["validate_codes"] = self.validate()
        a["verify_delivery"] = self.verify()
        cov = sh(self.repo, sys.executable, RECORD / "coverage.py", self.run_dir, check=False)
        rep = sh(self.repo, sys.executable, RECORD / "report.py", self.run_dir, check=False)
        a["coverage"], a["report"] = cov.returncode, rep.stdout.strip().splitlines()[-1]
        self.corruptions()
        if self.spec.get("flags", {}).get("dirty_cleanup"):
            (self.root / self.order[0] / "scratch.txt").write_text("left behind\n")
        code, cl = self.wt("cleanup", self.repo, "--root", self.root)
        self.fp["cleanup"] = {"exit": code, "removed": len(cl["removed"]), "kept": len(cl["kept"])}
        if code == 0:
            self.progress["workspace"]["removed"] = True
            self.save()
        a["verify_after_cleanup"] = self.verify()
        self.fp["main"] = sh(self.repo, "git", "rev-parse", "main").stdout.strip()
        self.fp["branches"] = sh(self.repo, "git", "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads/").stdout.split("\n")[:-1]
        self.fp["outcome"] = "delivered"
        return self.fp

    def conflict_probes(self, x, y):
        bad = next(w["commit"] for (n, k), w in sorted(self.ws.items()) if n == x and k == 1)
        code, r = self.wt("node", self.repo, "--slug", SLUG, "--node", "probe", "--attempt", 1, "--from", self.base, "--graph", self.run_dir / "graph.yaml",
                          "--upstream", f"{x}={bad}", "--upstream", f"{y}={self.accepted[y]}")
        self.fp["probes"]["fan_in_conflict"] = [code, r.get("conflicts")]
        code, r = self.wt("integrate", self.repo, "--slug", SLUG, "--attempt", 99, "--base", self.base, "--graph", self.run_dir / "graph.yaml",
                          "--accepted", f"{x}={bad}", "--accepted", f"{y}={self.accepted[y]}")
        self.fp["probes"]["integration_conflict"] = [code, r.get("conflicts")]

    # -- record corruptions ----------------------------------------------------------------
    def corruptions(self):
        from catalog import CORRUPTIONS  # noqa: imported here so the engine has no import cycle at load
        results = {}
        for name in self.spec.get("corruptions", []):
            fn = CORRUPTIONS[name]["apply"]
            d = self.run_dir.parent / f"{SLUG}-corrupt-{name}"
            shutil.copytree(self.run_dir, d)
            saved = (self.graph, self.rules, self.framing, self.progress, self.lessons, self.rows)
            self.graph, self.rules, self.framing, self.progress, self.lessons, self.rows = (copy.deepcopy(x) for x in saved)
            fn(self)
            self.save(d)
            self.graph, self.rules, self.framing, self.progress, self.lessons, self.rows = saved
            vcode, vcodes = self.validate(d)
            wcode, wcodes = self.verify(d)
            results[name] = {"validate": vcodes, "verify": wcodes}
            shutil.rmtree(d)
        self.fp["corruptions"] = results


def run_scenario(spec, tmp):
    sys.path.insert(0, str(HERE))
    return Scenario(spec, tmp).run()
