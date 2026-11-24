"""Synthetic scenario catalog: shapes, faults, a pairwise generator, an oracle, and record corruptions.

Everything here is a pure function of this file: the same code produces the same scenarios, the same expectations and the
same corruption assignments on every machine, so result files from two runs can be compared scenario by scenario.

Factors and levels (pairwise-covered over the valid combinations; see `pairwise()`):
  shape     single, chain, join, diamond, fan3, deep, wide
  fault     none, wrong, scope, empty, partial, secret, upstream_bad, conflict, late
  position  root, middle, sink   (where the fault lands; resolved per shape, and some faults need a dependent or a sibling)
  extra     none, identity       (the faulted node's first commit runs under a reset git identity)
  delivery  ff, squash, moved    (moved: the person commits to main during the run)
Named scenarios add compound faults and the start/cleanup refusals.

The oracle (`expected()`) is written from the prompt's rules, not from engine.py, so a disagreement between the two is a
finding about one of them.
"""
import hashlib
import itertools
import json

SHAPES = {
    "single": {"a": []},
    "chain": {"a": [], "b": ["a"], "c": ["b"]},
    "join": {"a": [], "b": [], "c": ["a", "b"]},
    "diamond": {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]},
    "fan3": {"a": [], "b": [], "c": [], "d": ["a", "b", "c"]},
    "deep": {"a": [], "b": ["a"], "c": ["b"], "d": ["c"], "e": ["d"]},
    "wide": {"a": [], "b": [], "c": [], "d": ["a"], "e": ["b"]},
}
FAULTS = ["none", "wrong", "scope", "empty", "partial", "secret", "upstream_bad", "conflict", "late"]
POSITIONS = ["root", "middle", "sink"]
EXTRAS = ["none", "identity"]
DELIVERIES = ["ff", "squash", "moved"]
FACTORS = [("shape", list(SHAPES)), ("fault", FAULTS), ("position", POSITIONS), ("extra", EXTRAS), ("delivery", DELIVERIES)]


def topo(nodes):
    order, done = [], set()
    while len(order) < len(nodes):
        ready = sorted(n for n, ups in nodes.items() if n not in done and set(ups) <= done)
        order.append(ready[0]); done.add(ready[0])
    return order


def related(nodes):
    """Pairs (x, y) where y is an ancestor or a descendant of x."""
    anc = {}
    for n in topo(nodes):
        anc[n] = set(nodes[n]) | {a for u in nodes[n] for a in anc[u]}
    return {(x, y) for x in nodes for y in nodes if x != y and (y in anc[x] or x in anc[y])}


def dependents(nodes, x):
    return [n for n in topo(nodes) if x in nodes[n]]


def resolve(shape, fault, position):
    """The node a fault lands on, and its sibling for a conflict; None when the combination is not valid."""
    nodes = SHAPES[shape]
    order = topo(nodes)
    if fault == "none":
        return ({"node": order[0]}) if position == "root" else None
    has_dep = {n: bool(dependents(nodes, n)) for n in nodes}
    where = {"root": [n for n in order if not nodes[n]],
             "middle": [n for n in order if nodes[n] and has_dep[n]],
             "sink": [n for n in order if not has_dep[n]]}[position]
    rel = related(nodes)
    for n in where:
        if fault == "upstream_bad" and not has_dep[n]:
            continue
        if fault == "conflict":
            sib = [y for y in order if y != n and (n, y) not in rel]
            if not sib:
                continue
            return {"node": n, "sibling": sib[0]}
        return {"node": n}
    return None


def make(shape, fault, position, extra, delivery, sid=None, faults=None, flags=None):
    nodes = SHAPES[shape]
    if faults is None:
        r = resolve(shape, fault, position)
        if r is None:
            return None
        faults = [] if fault == "none" else [{"kind": fault, **r}]
        if extra == "identity":
            if faults:
                faults[0]["identity"] = True
            else:
                faults = [{"kind": "none", "node": r["node"], "identity": True}]
    return {"id": sid or f"{shape}-{fault}-{position}-{extra}-{delivery}", "shape": shape, "nodes": nodes,
            "faults": faults, "delivery": delivery, "flags": flags or {}, "corruptions": []}


def pairwise():
    """Greedy all-pairs cover of the valid combinations, deterministic: ties go to the earliest combination."""
    valid = [c for c in itertools.product(*(levels for _, levels in FACTORS)) if make(*c) is not None]
    pairs = lambda c: {((i, c[i]), (j, c[j])) for i in range(len(c)) for j in range(i + 1, len(c))}
    need = set().union(*(pairs(c) for c in valid))
    chosen, covered = [], set()
    while covered != need:
        best = max(valid, key=lambda c: (len(pairs(c) - covered), -valid.index(c)))
        chosen.append(best); covered |= pairs(best)
    return chosen, len(need)


def named():
    out = [
        make("diamond", None, None, None, "ff", sid="named-compound-diamond",
             faults=[{"kind": "scope", "node": "b", "identity": True}, {"kind": "secret", "node": "c"}, {"kind": "late", "node": "d"}]),
        make("chain", None, None, None, "squash", sid="named-upstream-then-late",
             faults=[{"kind": "upstream_bad", "node": "a"}, {"kind": "late", "node": "b"}]),
        make("fan3", None, None, None, "moved", sid="named-three-faults-fan-in",
             faults=[{"kind": "wrong", "node": "a", "identity": True}, {"kind": "empty", "node": "b"}, {"kind": "partial", "node": "c"}]),
        make("wide", None, None, None, "ff", sid="named-conflict-and-late",
             faults=[{"kind": "conflict", "node": "a", "sibling": "b"}, {"kind": "late", "node": "e"}]),
        make("join", None, None, None, "ff", sid="named-dirty-start", faults=[], flags={"dirty_start": True}),
        make("chain", None, None, None, "ff", sid="named-dirty-cleanup", faults=[], flags={"dirty_cleanup": True}),
        make("join", None, None, None, "ff", sid="named-gate-byproduct", faults=[{"kind": "scope", "node": "b"}], flags={"byproduct": True}),
    ]
    return out


def expected(spec):
    """What the prompt's rules say must happen, derived from the scenario alone."""
    nodes = spec["nodes"]
    order = topo(nodes)
    faults = {f["node"]: f for f in spec["faults"]}
    if spec["flags"].get("dirty_start"):
        return {"outcome": "blocked_at_start", "calls": {("start", 3)}}
    att = {n: [] for n in order}
    calls = {("start", 0), ("node", 0), ("commit", 0), ("scope", 0), ("integrate", 0), ("verify", 0), ("history", 0), ("cleanup", 0)}
    for n in order:
        kind = faults.get(n, {}).get("kind")
        if kind in ("wrong", "scope", "empty", "secret", "conflict"):
            att[n] += [("first", "fail"), ("retry", "pass")]
        elif kind == "upstream_bad":
            if not att[n]:
                att[n] += [("first", "pass")]
        elif not att[n]:
            att[n] += [("first", "pass")]
        if kind == "upstream_bad":
            d = dependents(nodes, n)[0]
            att[n] += [("retry", "pass")]
            att[d] = [("first", "fail"), ("rebuild", "pass")]
        if kind == "empty":
            calls.add(("commit", 4))
        if kind in ("scope", "conflict", "wrong", "secret", "empty"):
            calls.add(("scope", 0))
        if kind in ("scope", "conflict"):
            calls.add(("scope", 1))
        if kind == "conflict":
            calls |= {("node", 3), ("integrate", 3)}
        if faults.get(n, {}).get("identity"):
            calls.add(("commit", 3))
    integrations = 1
    probes = {}
    for x in order:
        if faults.get(x, {}).get("kind") == "late":
            integrations += 1
            att[x].append(("retry", "pass"))
            for d in order:
                if d in {m for m in nodes if _reaches(nodes, x, m)}:
                    att[d].append(("rebuild", "pass"))
            probes["stale_integration_verify"] = [1, ["W05"]]
            calls.add(("verify", 1))
        if faults.get(x, {}).get("kind") == "conflict":
            path = [f"out/{faults[x]['sibling']}.txt"]
            probes["fan_in_conflict"] = [3, path]
            probes["integration_conflict"] = [3, path]
    secret = any(f["kind"] == "secret" for f in spec["faults"])
    squash = secret or spec["delivery"] == "squash"
    landed = "not_landed" if spec["delivery"] == "moved" else ("squashed" if squash else "fast_forward")
    calls.add(("land", 5 if landed == "not_landed" else 0))
    if secret:
        calls.discard(("history", 0)); calls.add(("history", 1))
    dirty = spec["flags"].get("dirty_cleanup")
    if dirty:
        calls.discard(("cleanup", 0)); calls.add(("cleanup", 1))
    if spec["flags"].get("byproduct"):
        calls.add(("exclude", 0))
    return {"outcome": "delivered", "attempts": att, "integrations": integrations, "history_failed": secret, "landed": landed,
            "calls": calls, "probes": probes, "cleanup_exit": 1 if dirty else 0}


def _reaches(nodes, x, m):
    frontier, seen = {x}, set()
    while frontier:
        nxt = {n for n, ups in nodes.items() if set(ups) & frontier} - seen
        if m in nxt:
            return True
        seen |= nxt; frontier = nxt
    return False


# -- record corruptions: each changes a copy of a finished record; the named codes must be among the findings ----------

def _newest_pass(s, node=None):
    rows = [r for r in s.rows if r["subject"]["kind"] == "node" and r["verdict"] == "pass" and (node is None or r["subject"]["node"] == node)]
    return max(rows, key=lambda r: (r["subject"]["node"] == s.order[0], r["attempt"])) if node is None else max(rows, key=lambda r: r["attempt"])


def _row(s, mode):
    for n in s.order:
        for a in s.fp["attempts"][n]:
            if a["mode"] == mode and (mode != "retry" or s.fp["attempts"][n][a["k"] - 2]["commit"] != s.base):
                return next(r for r in s.rows if r["subject"].get("node") == n and r["attempt"] == a["k"])


def _c_drop_workspace(s): _newest_pass(s, s.order[0]).pop("workspace")
def _c_outside(s): _newest_pass(s, s.order[0])["workspace"]["changed"].append("elsewhere.txt")
def _c_integration_branch(s): s.progress["workspace"]["integration_branch"] = f"graph/synth/integration/a9"
def _c_missing_commit(s): _newest_pass(s, s.order[0])["workspace"]["commit"] = "f" * 40
def _c_changed(s): _newest_pass(s, s.order[-1])["workspace"]["changed"] = []
def _c_author(s): s.progress["workspace"]["author"] = "Someone Else <else@synth.invalid>"
def _c_drop_landed(s): s.progress["workspace"].pop("landed")
def _c_landed_commit(s): s.progress["workspace"]["landed"]["commit"] = s.base
def _c_retry_base(s): _row(s, "retry")["workspace"]["base"] = s.base
def _c_rebuild_scope(s):
    r = _row(s, "rebuild"); r["workspace"]["scope_base"] = r["workspace"]["base"]
def _c_base_not_ancestor(s): s.progress["workspace"]["base"] = s.accepted[s.order[-1]]
def _c_person_branch(s): s.progress["workspace"]["person_branch"] = "no-such-branch"
def _c_branch_tip(s):
    r = _row(s, "retry"); n, k = r["subject"]["node"], r["attempt"]
    prev = next(x for x in s.rows if x["subject"].get("node") == n and x["attempt"] == k - 1)
    prev["workspace"]["branch"] = r["workspace"]["branch"]


_has_mode = lambda m: (lambda e: any(mode == m for att in e["attempts"].values() for mode, _ in att))
_has_retry_after_commit = lambda e, spec: any(f["kind"] in ("wrong", "scope", "secret", "conflict", "late", "upstream_bad") for f in spec["faults"])
CORRUPTIONS = {
    "drop-workspace": {"apply": _c_drop_workspace, "validate": {"X34"}, "verify": set(), "when": lambda e, s: True},
    "outside-writes": {"apply": _c_outside, "validate": {"X36"}, "verify": {"W04"}, "when": lambda e, s: True},
    "integration-branch": {"apply": _c_integration_branch, "validate": {"X37"}, "verify": set(), "when": lambda e, s: True},
    "missing-commit": {"apply": _c_missing_commit, "validate": set(), "verify": {"W01"}, "when": lambda e, s: True},
    "changed-list": {"apply": _c_changed, "validate": set(), "verify": {"W04"}, "when": lambda e, s: True},
    "author": {"apply": _c_author, "validate": set(), "verify": {"W10"}, "when": lambda e, s: True},
    "drop-landed": {"apply": _c_drop_landed, "validate": {"X37"}, "verify": set(), "when": lambda e, s: True},
    "landed-commit": {"apply": _c_landed_commit, "validate": {"X37"}, "verify": set(), "when": lambda e, s: e["landed"] == "fast_forward"},
    "squash-tree": {"apply": _c_landed_commit, "validate": set(), "verify": {"W09"}, "when": lambda e, s: e["landed"] == "squashed"},
    "retry-base": {"apply": _c_retry_base, "validate": {"X35"}, "verify": {"W08"}, "when": lambda e, s: _has_retry_after_commit(e, s)},
    "branch-tip": {"apply": _c_branch_tip, "validate": set(), "verify": {"W03"}, "when": lambda e, s: _has_retry_after_commit(e, s)},
    "base-not-ancestor": {"apply": _c_base_not_ancestor, "validate": set(), "verify": {"W06"}, "when": lambda e, s: len(s["nodes"]) > 1},
    "person-branch": {"apply": _c_person_branch, "validate": set(), "verify": {"W07"}, "when": lambda e, s: e["landed"] in ("fast_forward", "squashed")},
    "rebuild-scope-base": {"apply": _c_rebuild_scope, "validate": set(), "verify": {"W11"}, "when": lambda e, s: _has_mode("rebuild")(e)},
}
PER_CORRUPTION = 3


def scenarios():
    """The whole suite, in a fixed order, each with its corruptions assigned round-robin over the applicable scenarios."""
    chosen, _ = pairwise()
    suite = [make(*c) for c in chosen] + named()
    exp = {s["id"]: expected(s) for s in suite}
    for name, c in CORRUPTIONS.items():
        fits = [s for s in suite if exp[s["id"]]["outcome"] == "delivered" and c["when"](exp[s["id"]], s)]
        for _ in range(PER_CORRUPTION):
            if not fits:
                break
            fits.sort(key=lambda s: (len(s["corruptions"]), hashlib.sha256((name + s["id"]).encode()).hexdigest()))
            fits.pop(0)["corruptions"].append(name)
    return suite


def suite_digest(suite):
    return hashlib.sha256(json.dumps(suite, sort_keys=True).encode()).hexdigest()[:16]


def check(spec, fp):
    """Compare a fingerprint with the oracle. Returns the list of mismatches (empty: the scenario behaved as specified)."""
    e = expected(spec)
    bad = []
    got_calls = {tuple(c) for c in fp["calls"]}
    if not fp.get("outcome", "").startswith(e["outcome"]):
        bad.append(f"outcome {fp.get('outcome')!r}, expected {e['outcome']}")
    for c in sorted(e["calls"]):
        if c not in got_calls:
            bad.append(f"no worktrees.py {c[0]} call exited {c[1]}")
    if e["outcome"] != "delivered":
        return bad
    for n, want in e["attempts"].items():
        got = [(a["mode"], a["verdict"]) for a in fp["attempts"][n]]
        if got != want:
            bad.append(f"{n}: attempts {got}, expected {want}")
    if len(fp["integration"]) != e["integrations"]:
        bad.append(f"{len(fp['integration'])} integrations, expected {e['integrations']}")
    if bool(fp["history"]["failed_index"]) != e["history_failed"]:
        bad.append(f"history failed {fp['history']['failed_index']}, expected {'some' if e['history_failed'] else 'none'}")
    if fp["landed"]["kind"] != e["landed"]:
        bad.append(f"landed {fp['landed']['kind']}, expected {e['landed']}")
    for k, v in e["probes"].items():
        if fp["probes"].get(k) != v:
            bad.append(f"probe {k}: {fp['probes'].get(k)}, expected {v}")
    a = fp["audits"]
    for key, want in (("validate_audit1", 0), ("validate_delivery", 0), ("coverage", 0), ("report", "status: complete"),
                      ("verify_audit1", [0, []]), ("verify_delivery", [0, []]), ("verify_after_cleanup", [0, []])):
        got = list(a[key]) if isinstance(a[key], tuple) else a[key]
        if got != want:
            bad.append(f"{key}: {got}, expected {want}")
    if a["evidence"][1:] != [0, 0]:
        bad.append(f"evidence audit miscited/unfound {a['evidence'][1:]}")
    for k in ("k1", "k2"):
        if fp["integration"][-1]["accept"].get(k) != "pass":
            bad.append(f"final acceptance {k} {fp['integration'][-1]['accept'].get(k)}")
    if fp["cleanup"]["exit"] != e["cleanup_exit"]:
        bad.append(f"cleanup exit {fp['cleanup']['exit']}, expected {e['cleanup_exit']}")
    for name in spec["corruptions"]:
        c, got = CORRUPTIONS[name], fp["corruptions"].get(name, {})
        if not c["validate"] <= set(got.get("validate", [])) or not c["verify"] <= set(got.get("verify", [])):
            bad.append(f"corruption {name}: validate {got.get('validate')} verify {got.get('verify')}, expected ⊇ {sorted(c['validate'])} / {sorted(c['verify'])}")
    return bad
