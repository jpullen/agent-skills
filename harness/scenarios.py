#!/usr/bin/env python3
"""harness/scenarios.py — the synthetic scenario suite: generate, run, compare.

  python3 harness/scenarios.py list                         the suite: id, faults, corruptions
  python3 harness/scenarios.py run [--out R.json] [--only S ...] [--sample N] [--jobs J] [--compare BASE.json]
  python3 harness/scenarios.py compare OLD.json NEW.json     scenario-by-scenario differences
  python3 harness/scenarios.py coverage R.json               what the suite exercised, against what exists

Each scenario is a whole v3.6 run in a throwaway git repository, driven by a scripted lead (no model calls), followed by
record corruptions on copies of the finished record. A scenario passes when its fingerprint matches the oracle in
synth/catalog.py. The fingerprint holds no path, time or random value, and git runs with fixed dates and no user
config, so every commit id is reproducible: two result files differ only where behaviour differs.

Exit codes: run — 0 if every scenario matches its oracle and (with --compare) every fingerprint equals the baseline's;
1 otherwise. compare — 0 if identical, 1 if any scenario differs, appeared or disappeared. 2 usage.
"""
import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYNTH = ROOT / "plugins" / "graph-prompt" / "skills" / "graph" / "scripts" / "synth"
sys.path.insert(0, str(SYNTH))
import catalog  # noqa: E402

VOLATILE = {"timing"}


def _one(spec):
    sys.path.insert(0, str(SYNTH))
    import engine
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            fp = json.loads(json.dumps(engine.Scenario(spec, tmp).run()))
            error = None
        except Exception as e:  # a crash is a result, not a harness failure
            fp, error = {"id": spec["id"], "calls": []}, f"{type(e).__name__}: {e}"[:2000]
    mismatches = [f"engine error: {error}"] if error else catalog.check(spec, fp)
    return spec["id"], {"fingerprint": fp, "mismatches": mismatches, "timing": round(time.time() - t0, 1)}


def select(suite, only, sample):
    if only:
        suite = [s for s in suite if any(o in s["id"] for o in only)]
    if sample:
        step = max(1, len(suite) // sample)
        suite = suite[::step][:sample]
    return suite


def run(a):
    suite = select(catalog.scenarios(), a.only, a.sample)
    t0 = time.time()
    results = {}
    with ProcessPoolExecutor(a.jobs) as ex:
        for sid, res in ex.map(_one, suite):
            results[sid] = res
            mark = "PASS" if not res["mismatches"] else "FAIL"
            print(f"{mark}  {sid:44} {res['timing']:6.1f}s" + ("" if not res["mismatches"] else "  " + res["mismatches"][0][:110]), flush=True)
    doc = {"suite_digest": catalog.suite_digest(catalog.scenarios()), "scenarios": dict(sorted(results.items())),
           "coverage": coverage(results, suite)}
    failed = [s for s, r in results.items() if r["mismatches"]]
    print(f"\n{len(results) - len(failed)} of {len(results)} scenarios match the oracle ({time.time() - t0:.0f}s)")
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    drift = 0
    if a.compare:
        base = json.loads(pathlib.Path(a.compare).read_text())
        drift = compare_docs(base, doc, only=set(results))
    print_coverage(doc["coverage"])
    return 1 if failed or drift else 0


def strip(res):
    return {k: v for k, v in res.items() if k not in VOLATILE}


def diff(a, b, path=""):
    if type(a) != type(b):
        return [f"{path}: {json.dumps(a)[:80]} → {json.dumps(b)[:80]}"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k), b.get(k), f"{path}.{k}" if path else k) if k in a and k in b else [f"{path}.{k}: {'added' if k in b else 'removed'}"]
        return out
    if isinstance(a, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {json.dumps(a)[:80]} → {json.dumps(b)[:80]}"]


def compare_docs(old, new, only=None):
    o, n = old["scenarios"], new["scenarios"]
    ids = sorted((set(o) | set(n)) if only is None else only)
    changed = 0
    if old.get("suite_digest") != new.get("suite_digest"):
        print(f"suite changed: digest {old.get('suite_digest')} → {new.get('suite_digest')} (catalog.py was edited; expect additions and removals)")
    for sid in ids:
        if sid not in o or sid not in n:
            print(f"{'NEW ' if sid in n else 'GONE'}  {sid}")
            changed += 1
            continue
        d = diff(strip(o[sid]), strip(n[sid]))
        if d:
            changed += 1
            print(f"DIFF  {sid}: {len(d)} field(s)")
            for line in d[:8]:
                print(f"      {line}")
            if len(d) > 8:
                print(f"      ... {len(d) - 8} more")
    slow = [(sid, o[sid]["timing"], n[sid]["timing"]) for sid in ids if sid in o and sid in n and n[sid]["timing"] > 2 * o[sid]["timing"] + 5]
    for sid, t0, t1 in slow:
        print(f"SLOW  {sid}: {t0}s → {t1}s (not a failure)")
    print(f"compare: {len(ids) - changed} of {len(ids)} scenarios identical to the baseline")
    return changed


# -- coverage: what the suite exercised, against what exists ------------------------------------------------------

def universe():
    src = (SYNTH.parent / "worktrees.py").read_text()
    schema = json.loads((ROOT / "plugins/graph-prompt/skills/graph-record/scripts/graph-record.schema.json").read_text())
    exits = {"start": {0, 3}, "exclude": {0}, "node": {0, 3}, "commit": {0, 3, 4}, "scope": {0, 1}, "integrate": {0, 3},
             "verify": {0, 1}, "history": {0, 1}, "land": {0, 5}, "cleanup": {0, 1}}
    w = sorted(set(re.findall(r'f"(W\d\d) ', src)))
    x = sorted(r.split()[0] for r in schema["x-crossfile"] if r.split()[0] in ("X34", "X35", "X36", "X37"))
    transitions = ["first pass", "retry after cause (a)", "attempt that changed nothing", "builder stopped after writing", "scope diff fails",
                   "fan-in conflict aborted", "integration conflict aborted", "cause (b): upstream reopened", "rebuild with --carry",
                   "correction after integration", "stale integration found by verify", "identity refused and restored",
                   "history gate fails", "landed fast-forward", "landed squashed", "not landed (branch moved)", "start refused",
                   "cleanup keeps a dirty worktree"]
    return exits, w, x, transitions


def coverage(results, suite):
    specs = {s["id"]: s for s in suite}
    exits, wcodes, xcodes, transitions = universe()
    seen_exit, seen_w, seen_x, seen_t = set(), set(), set(), set()
    for sid, r in results.items():
        fp = r["fingerprint"]
        seen_exit |= {(c[0], c[1]) for c in fp.get("calls", [])}
        for c in (fp.get("corruptions") or {}).values():
            seen_w |= set(c.get("verify", [])); seen_x |= set(c.get("validate", []))
        for k in ("stale_integration_verify",):
            if k in fp.get("probes", {}):
                seen_w |= set(fp["probes"][k][1])
        att = [a for lst in fp.get("attempts", {}).values() for a in lst]
        t = seen_t
        if any(a["mode"] == "first" and a["verdict"] == "pass" for a in att): t.add("first pass")
        if any(a["mode"] == "retry" for a in att): t.add("retry after cause (a)")
        if any(a["behavior"] == "empty" for a in att): t.add("attempt that changed nothing")
        if any(a["behavior"] == "partial" for a in att): t.add("builder stopped after writing")
        if any(a["outside"] for a in att): t.add("scope diff fails")
        if fp.get("probes", {}).get("fan_in_conflict", [0])[0] == 3: t.add("fan-in conflict aborted")
        if fp.get("probes", {}).get("integration_conflict", [0])[0] == 3: t.add("integration conflict aborted")
        if any(a["gate"].startswith("UPSTREAM") for a in att): t.add("cause (b): upstream reopened")
        if any(a["mode"] == "rebuild" for a in att): t.add("rebuild with --carry")
        if len(fp.get("integration", [])) > 1: t.add("correction after integration")
        if fp.get("probes", {}).get("stale_integration_verify", [0])[0] == 1: t.add("stale integration found by verify")
        if ["commit", 3] in fp.get("calls", []): t.add("identity refused and restored")
        if fp.get("history", {}).get("failed_index"): t.add("history gate fails")
        kind = fp.get("landed", {}).get("kind")
        t.add({"fast_forward": "landed fast-forward", "squashed": "landed squashed", "not_landed": "not landed (branch moved)"}.get(kind, "first pass"))
        if str(fp.get("outcome", "")).startswith("blocked_at_start"): t.add("start refused")
        if fp.get("cleanup", {}).get("kept"): t.add("cleanup keeps a dirty worktree")
    all_exits = {(s, c) for s, cs in exits.items() for c in cs}
    _, npairs = catalog.pairwise()
    return {"exit_codes": {"covered": sorted(f"{s}:{c}" for s, c in all_exits & seen_exit), "missing": sorted(f"{s}:{c}" for s, c in all_exits - seen_exit)},
            "verify_findings": {"covered": sorted(set(wcodes) & seen_w), "missing": sorted(set(wcodes) - seen_w)},
            "worktree_rules": {"covered": sorted(set(xcodes) & seen_x), "missing": sorted(set(xcodes) - seen_x)},
            "transitions": {"covered": [t for t in transitions if t in seen_t], "missing": [t for t in transitions if t not in seen_t]},
            "factor_pairs": npairs, "scenarios": len(results)}


def print_coverage(c):
    print("\ncoverage")
    for key in ("exit_codes", "verify_findings", "worktree_rules", "transitions"):
        cov, miss = len(c[key]["covered"]), len(c[key]["missing"])
        print(f"  {key:16} {cov}/{cov + miss}" + (f"   missing: {', '.join(c[key]['missing'])}" if miss else ""))
    print(f"  factor pairs     {c['factor_pairs']}/{c['factor_pairs']} (all-pairs cover over the valid combinations; {c['scenarios']} scenarios run)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("run")
    p.add_argument("--out"); p.add_argument("--only", nargs="+"); p.add_argument("--sample", type=int)
    p.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2)); p.add_argument("--compare")
    p = sub.add_parser("compare"); p.add_argument("old"); p.add_argument("new")
    p = sub.add_parser("coverage"); p.add_argument("results")
    a = ap.parse_args()
    if a.cmd == "list":
        suite = catalog.scenarios()
        for s in suite:
            print(f"{s['id']:44} {', '.join(f['kind'] + '@' + f['node'] + ('+identity' if f.get('identity') else '') for f in s['faults']) or '-':34} {' '.join(s['corruptions'])}")
        print(f"\n{len(suite)} scenarios, digest {catalog.suite_digest(suite)}")
        return 0
    if a.cmd == "run":
        return run(a)
    if a.cmd == "compare":
        return 1 if compare_docs(json.loads(pathlib.Path(a.old).read_text()), json.loads(pathlib.Path(a.new).read_text())) else 0
    if a.cmd == "coverage":
        print_coverage(json.loads(pathlib.Path(a.results).read_text())["coverage"])
        return 0


if __name__ == "__main__":
    sys.exit(main())
