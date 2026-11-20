"""A scripted lead for end-to-end tests of prompt v3.6's worktree machinery.

It does what the prompt's lead does, in the prompt's order, with no model in the loop: it calls
worktrees.py for every git step, runs the gates itself, writes the run record after every terminal
state, and runs both audits. Builders are plain functions (see builders.py), so a run is
deterministic and costs no tokens. What this exercises is the kit — worktrees.py, the schema,
validate.py, coverage.py, report.py — against real git state and a real record. What it cannot
exercise is a model's behaviour as lead, builder or reviewer; that stays with calibration runs.
"""
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
FIXTURE = HERE / "fixture"
MODELS = "tier-low,tier-mid,tier-high"
SLUG = "e2e-units"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def sh(cwd, *args, check=True):
    r = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, env=ENV)
    if check and r.returncode != 0:
        raise AssertionError(f"{args}: exit {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


class Lead:
    NODES = {
        "table": {"purpose": "Length factors and conversion", "shape": ["factors", "convert"], "writes": ["units/table.py"], "upstream": {}},
        "parse": {"purpose": "Argument parsing", "shape": ["parse_args"], "writes": ["units/parse.py"], "upstream": {}},
        "cli": {"purpose": "Command-line entry point", "shape": ["main"], "writes": ["cli.py"],
                "upstream": {"table": ["convert"], "parse": ["parse_args"]}},
    }

    def __init__(self, tmp, table_gate="test_table.py"):
        self.repo = pathlib.Path(tmp) / "repo"
        self.run_dir = self.repo / ".graph" / SLUG
        self.code = self.run_dir / "code"
        self.table_gate = table_gate
        self.consumed = 0
        self.attempts = {}      # node -> newest attempt number
        self.ws = {}            # (node, attempt) -> row workspace
        self.accepted = {}      # node -> accepted commit
        self.scope_base = {}    # node -> current scope base
        self.integration = None
        self._init_repo()
        self._start()
        self._write_record()

    # -- setup -----------------------------------------------------------------------------
    def _init_repo(self):
        (self.repo / "units").mkdir(parents=True)
        sh(self.repo, "git", "init", "-q", "-b", "main")
        sh(self.repo, "git", "config", "user.name", "e2e lead")
        sh(self.repo, "git", "config", "user.email", "lead@e2e.invalid")
        shutil.copy(FIXTURE / "SPEC.md", self.repo / "SPEC.md")
        (self.repo / "units" / "__init__.py").write_text("")
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "commit", "-q", "-m", "units: spec")
        shutil.copytree(FIXTURE / "gates", self.code)
        shutil.copytree(FIXTURE / "stub", self.code / "stub")

    def wt(self, *args):
        r = sh(self.repo, sys.executable, SCRIPTS / "worktrees.py", *args, check=False)
        return r.returncode, json.loads(r.stdout)

    def _start(self):
        code, s = self.wt("start", self.repo, "--slug", SLUG, "--run-dir", self.run_dir,
                          "--scope", "units", "cli.py", "--exclude", "__pycache__/")
        assert code == 0, s
        self.start = s
        self.base = s["base"]
        self.root = pathlib.Path(s["root"])
        # baseline (principles): every gate is red by assertion against the stub, every acceptance item red at base
        self.red = {}
        for n in self.NODES:
            r = sh(self.code / "stub", sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", self.code / self.gate_file(n), check=False)
            assert r.returncode == 1, f"{n} gate is not red by assertion at baseline:\n{r.stdout}"
            self.red[n] = r.stdout.strip().splitlines()[-1]
        r = sh(self.repo, sys.executable, self.code / "acceptance.py", s["baseline"], check=False)
        assert r.returncode == 1 and r.stdout.count("fail") == 4, r.stdout

    def gate_file(self, node):
        return self.table_gate if node == "table" else f"test_{node}.py"

    # -- record ----------------------------------------------------------------------------
    def _write_record(self):
        def node(n, spec):
            split = ({"kind": "inputs_differ", "nodes": sorted(spec["upstream"])} if spec["upstream"]
                     else {"kind": "parallel", "nodes": [x for x in ("table", "parse") if x != n]})
            return {"id": n, "purpose": spec["purpose"], "does": [{"imperative": f"write {s}", "produces": s} for s in spec["shape"]],
                    "shape": spec["shape"], "split_reason": split,
                    "reads": {"sources": True, "upstream": [{"node": u, "sections": sec} for u, sec in spec["upstream"].items()]},
                    "writes": spec["writes"], "needs": [], "kind": "judgment",
                    "checks": [{"id": f"{n}-gate", "type": "exec", "content": f"pytest {self.gate_file(n)} in the node's worktree, plus the scope diff",
                                "fails_when": "any gate test fails or the scope diff lists a path outside writes", "exec_available": "yes"}],
                    "rules": {"kind": "judgment"}, "model": {"tier": "tier-low", "tier_rule": [], "escalations": 0}}
        self.graph = {"nodes": [node(n, s) for n, s in self.NODES.items()]}
        quotes = {"s1": "`units/table.py` defines `FACTORS`", "s2": "an unknown `src` or `dst` raises `ValueError`",
                  "s3": "raises `SystemExit` with code 2", "s4": "formatted with `%g` to stdout and returns 0",
                  "s5": "Only the standard library is used."}
        self.rules = {"rules": [{"id": k, "spec": "SPEC.md", "rule": f"SPEC.md {k.upper()}", "section": k.upper(), "quote": q,
                                 "concerns": ["deliverable"]} for k, q in quotes.items()]}
        self.framing = {"problem": "Build the units CLI from SPEC.md as two parallel nodes and a join, under worktree isolation.",
                        "goals": ["SPEC.md S1-S5 hold on the merged deliverable"], "constraints": ["standard library only", "autonomous mode"],
                        "assumptions": [{"id": "a1", "text": "%g of 5000.0 prints 5000", "assumed": "yes"}],
                        "unknowns": [{"id": "u1", "text": "whether cli catches SystemExit", "changes_outcome": False, "disposition": "assumed"}],
                        "risks": [{"id": "r1", "text": "a builder writes outside its writes", "guarded_by": {"kind": "gate", "node": "parse", "check": "parse-gate"}}]}
        self.rows = []
        for n in self.NODES:
            self.rows.append(self._node_row_proto(n, 1))
        exercises = {"k1": ["s1", "s2", "s4"], "k2": ["s1", "s4"], "k3": ["s2", "s4"], "k4": ["s1", "s2", "s3", "s4", "s5"]}
        for k, e in exercises.items():
            self.rows.append({"subject": {"kind": "acceptance", "item": k}, "attempt": 1, "requirement": f"acceptance item {k}", "type": "exec",
                              "isolation": {"kind": "not_run", "reason": "integration not run"}, "fails_when": f"acceptance.py prints '{k} fail'",
                              "red_evidence": {"kind": "checks_baseline", "summary": f"{k} fail on the baseline worktree"},
                              "verdict": "unresolved", "evidence": {"kind": "not_run", "reason": "integration not run"}, "exercises": e})
        self.progress = {
            "enforcement": {"kind": "instruction_only"},
            "graph": {k: [] for k in ("accepted", "running", "failed", "blocked", "dissent", "escalated", "not_started")},
            "outputs": [], "decisions": [{"kind": "approval_default", "reason": "autonomous mode"},
                                         {"kind": "other", "reason": "__pycache__/ excluded before the first gate (gate byproduct)"}],
            "assumptions": [{"id": "a1", "assumed": "yes"}], "open_issues": [], "unchecked_rules": [], "subagents": [],
            "audits": {"wellformed": {"exit_code": 0, "isolation": "na_code"},
                       "evidence": {"isolation": {"kind": "not_run", "reason": "not reached"}, "rows": 0, "miscited": 0, "unfound": 0, "verdict": "not_run", "notes": []}},
            "hypotheses": [], "usage": {"limit": 20, "unit": "node_runs", "consumed": 0, "lead_tokens": None},
            "next_action": {"kind": "node", "node": "table"},
            "workspace": {k: self.start[k] for k in ("kind", "repo", "base", "person_branch", "root")}}
        self.progress["graph"]["not_started"] = list(self.NODES)
        self.lessons = {"entries": []}
        self.save()

    def _node_row_proto(self, n, attempt):
        return {"subject": {"kind": "node", "node": n, "check": f"{n}-gate"}, "attempt": attempt,
                "requirement": f"{n} gate tests pass and its changes stay inside writes", "type": "exec",
                "isolation": {"kind": "not_run", "reason": "not dispatched"},
                "fails_when": "any gate test fails or the scope diff lists a path outside writes",
                "red_evidence": {"kind": "assertion_failure", "test_path": str(self.code / self.gate_file(n)), "summary": self.red[n],
                                 "stub_path": str(self.code / "stub")},
                "verdict": "unresolved", "evidence": {"kind": "not_run", "reason": "not dispatched"}}

    def save(self):
        for name in ("graph", "rules", "framing", "progress", "lessons"):
            (self.run_dir / f"{name}.yaml").write_text(yaml.safe_dump(getattr(self, name), sort_keys=False, width=200))
        (self.run_dir / "checks.yaml").write_text(yaml.safe_dump({"rows": self.rows}, sort_keys=False, width=200))

    # -- one node attempt ------------------------------------------------------------------
    def attempt(self, node, builder, cause=None):
        """Dispatch one attempt of `node` to the scripted `builder`; commit, scope-diff, gate, record. Returns the verdict."""
        n = self.attempts.get(node, 0) + 1
        prev = self.ws.get((node, n - 1))
        rebuild = cause == "upstream_field"
        if n == 1 or rebuild:
            frm, ups = self.base, {u: self.accepted[u] for u in self.NODES[node]["upstream"]}
        else:
            frm, ups = prev["commit"], {}
        args = ["node", self.repo, "--slug", SLUG, "--node", node, "--attempt", n, "--from", frm, "--graph", self.run_dir / "graph.yaml"]
        if rebuild:
            args += ["--carry", prev["commit"]]
        for u, sha in ups.items():
            args += ["--upstream", f"{u}={sha}"]          # repeated flags, as a lead writes them (RF-64)
        code, made = self.wt(*args)
        assert code == 0, made
        tree, base = pathlib.Path(made["worktree"]), made["base"]
        if n == 1 or rebuild:
            self.scope_base[node] = made["upstream_base"]  # RF-62/RF-67: what the upstreams provide, before the node's own work
        if n > 1:
            self.progress["hypotheses"].append({"node": node, "before_attempt": n, "cause": cause or "builder_error",
                                                "disconfirmation": "the retry's gate fails on the same section"})
        builder(tree)
        self.consumed += 1
        self.progress["subagents"].append({"id": f"scripted-{node}-{n}", "role": "builder", "node": node, "tier": "tier-low"})
        code, c = self.wt("commit", tree, "--message", f"graph({SLUG}): {node} a{n}")
        commit = c["commit"] if code == 0 else base       # RF-65: an attempt that changed nothing takes its base as its commit
        assert code in (0, 4), c
        sb = self.scope_base[node]
        scode, scope = self.wt("scope", tree, "--base", sb, "--commit", commit, "--graph", self.run_dir / "graph.yaml", "--node", node)
        gate_cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(self.code / self.gate_file(node))]
        gate = sh(tree, *gate_cmd, check=False)
        actual = gate.returncode or scode
        verdict = "pass" if actual == 0 else "fail"
        ws = {"branch": made["branch"], "base": base, "scope_base": sb, "commit": commit, "changed": scope["changed"]}
        row = self._node_row_proto(node, n)
        row.update(isolation={"kind": "na_exec"}, verdict=verdict, workspace=ws, evidence={
            "kind": "exec", "expected_exit": 0, "actual_exit": actual,
            "command": f"cd {tree} && {' '.join(gate_cmd)} && {sys.executable} {SCRIPTS / 'worktrees.py'} scope {tree} --base {sb} --commit {commit} "
                       f"--graph {self.run_dir / 'graph.yaml'} --node {node}",
            "output": f"{(gate.stdout.strip().splitlines() or ['no output'])[-1]}; scope outside {scope['outside']}"})
        if n == 1:
            self.rows[next(i for i, r in enumerate(self.rows) if r["subject"].get("node") == node)] = row
        else:
            self.rows.insert(max(i for i, r in enumerate(self.rows) if r["subject"].get("node") == node) + 1, row)
        self.attempts[node], self.ws[(node, n)] = n, ws
        g = self.progress["graph"]
        for lst in g.values():
            if node in lst:
                lst.remove(node)
        if verdict == "pass":
            self.accepted[node] = commit
            g["accepted"].append(node)
            if self.NODES[node]["writes"][0] not in self.progress["outputs"]:
                self.progress["outputs"] += self.NODES[node]["writes"]
        else:
            self.accepted.pop(node, None)
            g["running"].append(node)
        self.progress["usage"]["consumed"] = self.consumed
        self.progress["next_action"] = {"kind": "node", "node": node if verdict == "fail" else next(iter(g["not_started"]), node)}
        self.save()
        return verdict, scope

    def reopen(self, node):
        """Cause (b): an accepted upstream is reopened; it leaves the accepted list until re-accepted."""
        g = self.progress["graph"]
        g["accepted"].remove(node); g["running"].append(node)
        self.accepted.pop(node)
        self.save()

    # -- convergence -----------------------------------------------------------------------
    def integrate(self):
        k = (self.integration or {}).get("attempt", 0) + 1
        args = ["integrate", self.repo, "--slug", SLUG, "--attempt", k, "--base", self.base, "--graph", self.run_dir / "graph.yaml"]
        for node, sha in sorted(self.accepted.items(), reverse=True):   # deliberately not topological: the program orders them
            args += ["--accepted", f"{node}={sha}"]
        code, ig = self.wt(*args)
        if code != 0:
            return code, ig
        cmd = [sys.executable, str(self.code / "acceptance.py"), ig["worktree"]]
        r = sh(self.repo, *cmd, check=False)
        (self.run_dir / "integration.out").write_text(r.stdout)
        self.consumed += 1
        ws = {"branch": ig["branch"], "base": self.base, "scope_base": self.base, "commit": ig["commit"], "changed": ig["changed"]}
        lines = dict(l.split() for l in r.stdout.strip().splitlines())
        fresh = []
        for item in ("k1", "k2", "k3", "k4"):
            proto = next(x for x in self.rows if x["subject"].get("item") == item)
            row = json.loads(json.dumps(proto))
            row.update(attempt=k, isolation={"kind": "na_exec"}, verdict=lines[item], workspace=ws,
                       evidence={"kind": "exec", "command": " ".join(cmd), "expected_exit": 0, "actual_exit": r.returncode, "output": f"{item} {lines[item]}"})
            fresh.append(row)
        fresh.append({"subject": {"kind": "integration"}, "attempt": k, "requirement": "every acceptance item passes on the integration branch",
                      "type": "exec", "isolation": {"kind": "na_exec"}, "fails_when": "acceptance.py exits non-zero",
                      "red_evidence": {"kind": "checks_baseline", "summary": "k1-k4 fail on the baseline worktree"},
                      "verdict": "pass" if r.returncode == 0 else "fail", "workspace": ws,
                      "evidence": {"kind": "exec", "command": " ".join(cmd), "expected_exit": 0, "actual_exit": r.returncode,
                                   "output": " / ".join(f"{i} {v}" for i, v in lines.items())}})
        if k == 1:
            self.rows = [x for x in self.rows if x["subject"]["kind"] == "node"] + fresh
        else:
            self.rows += fresh
            self.progress["hypotheses"] += [{"node": who, "before_attempt": k, "cause": "upstream_field", "disconfirmation": "the item fails again"}
                                            for who in ("k1", "k2", "k3", "k4", "integration")]
        self.integration = {"attempt": k, **ig}
        self.progress["workspace"]["integration_branch"] = ig["branch"]
        self.progress["usage"]["consumed"] = self.consumed
        self.save()
        return r.returncode, ig

    # -- audits and delivery ---------------------------------------------------------------
    def validate(self):
        r = sh(self.repo, sys.executable, RECORD / "validate.py", self.run_dir, "--models", MODELS, "--all", check=False)
        return r.returncode, r.stdout

    def verify(self):
        return self.wt("verify", self.run_dir)

    def evidence_audit(self):
        """The fresh-context audit, scripted: rerun every newest pass row's command exactly as cited."""
        newest = {}
        for r in self.rows:
            if r["verdict"] == "pass" and r["type"] == "exec":
                s = r["subject"]
                key = (s["kind"], s.get("node"), s.get("item"))
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
        rows = len(newest)
        self.progress["subagents"].append({"id": "scripted-audit", "role": "evidence_audit", "phase": "audit", "tier": "tier-mid"})
        self.progress["audits"]["evidence"] = {"isolation": {"kind": "fresh_subagent", "subagent": "scripted-audit"}, "rows": rows,
                                               "miscited": miscited, "unfound": unfound,
                                               "verdict": "pass" if rows == 0 or (miscited + unfound) / rows <= 0.10 else "fail", "notes": []}
        self.progress["usage"]["consumed"] = self.consumed
        self.save()
        return rows, miscited, unfound

    def deliver(self):
        code, landed = self.wt("land", self.repo, "--commit", self.integration["commit"], "--branch", self.start["person_branch"])
        self.progress["workspace"]["landed"] = landed
        self.progress["next_action"] = {"kind": "delivery"}
        self.lessons = {"entries": [{"node": n, "evidence": f"gate passed at attempt {a}", "tier": "tier-low", "tier_rule": [], "attempt": a,
                                     "confirmed_in": 1, "promoted": False} for n, a in self.attempts.items()]}
        self.save()
        return code, landed

    def cleanup(self):
        code, out = self.wt("cleanup", self.repo, "--root", self.root)
        if code == 0:
            self.progress["workspace"]["removed"] = True
            self.save()
        return code, out

    def report(self):
        cov = sh(self.repo, sys.executable, RECORD / "coverage.py", self.run_dir, check=False)
        rep = sh(self.repo, sys.executable, RECORD / "report.py", self.run_dir, check=False)
        return cov.returncode, rep.returncode, rep.stdout.strip().splitlines()[-1]
