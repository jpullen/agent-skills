#!/usr/bin/env python3
"""harness/run.py — the one entry point for testing the graph-prompt kit.

usage: python3 harness/run.py [fast|standard|full] [--only STEP ...] [--list] [--json PATH]

Tiers (each includes the one before):
  fast      consistency checks, the record scripts' suite, the worktrees.py suite, both bundled
            examples through validate / coverage / report, the Codex adapter's suite.                              (~1.5 min)
  standard  + the end-to-end scenarios: a scripted lead drives whole v3.6 runs in throwaway
            git repositories, no model calls; + the synthetic suite's own tests and a 12-scenario
            sample of it, compared with the committed baseline. The default; run it before every
            push.                                                                        (~3 min)
  full      + the generated-mutant regression of validate.py on both examples, the mutation
            run over worktrees.py against its allowlist of equivalent mutants, and all synthetic
            scenarios compared with the baseline. Run it before a release and whenever the
            schema, validate.py or worktrees.py changes.                                (~17 min)

A step passes when its exit code is the expected one and, where given, its output matches a pattern
(for example `gaps 0; over-strict 0`). Exit 0 when every selected step passes, 1 otherwise, 2 on a
usage error. Needs python3, git >= 2.31, pytest, pyyaml, jsonschema.

What this harness does not do: run a model. Whether a model follows the prompt as lead, builder or
reviewer is measured by calibration runs, pre-registered in CALIBRATION-LOG.md; TEST-MATRIX.md lists
what those have and have not covered. harness/README.md says which belongs where.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORD = ROOT / "plugins" / "graph-prompt" / "skills" / "graph-record" / "scripts"
GRAPH = ROOT / "plugins" / "graph-prompt" / "skills" / "graph" / "scripts"
CODEX = ROOT / "compat" / "codex"
PY = sys.executable
PYTEST = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
MODELS = "haiku,sonnet,opus"
TIERS = ["fast", "standard", "full"]


def steps(tmp):
    def example(name):
        d = str(RECORD / name)
        return [
            (f"{name}: validate", "fast", RECORD, [PY, "validate.py", d, "--models", MODELS], 0, r"^OK .*schema \+ crossfile hold"),
            (f"{name}: coverage", "fast", RECORD, [PY, "coverage.py", d], 0, r"uncovered=0"),
            (f"{name}: report", "fast", RECORD, [PY, "report.py", d], 0, r"status: complete\s*$"),
        ]
    fixtures = lambda name: (f"{name}: generated mutants", "full", RECORD,
                             [PY, "gen_fixtures.py", str(RECORD / name), os.path.join(tmp, f"fx-{name}"), "--models", MODELS],
                             0, r"gaps 0; over-strict 0")
    return [
        ("consistency", "fast", ROOT, PYTEST + ["harness/test_consistency.py"], 0, None),
        ("record scripts suite", "fast", RECORD, PYTEST, 0, None),
        ("worktrees.py suite", "fast", GRAPH, PYTEST + ["test_worktrees.py"], 0, None),
        *example("example"), *example("example-worktree"),
        ("codex adapter suite", "fast", CODEX, PYTEST, 0, None),
        ("end-to-end scenarios", "standard", GRAPH, PYTEST + ["test_e2e_run.py"], 0, None),
        ("synthetic suite tests", "standard", GRAPH, PYTEST + ["test_synth.py"], 0, None),
        ("synthetic scenarios (sample)", "standard", ROOT, [PY, "harness/scenarios.py", "run", "--sample", "12", "--compare", "harness/scenarios-baseline.json"],
         0, r"12 of 12 scenarios match the oracle"),
        fixtures("example"), fixtures("example-worktree"),
        ("synthetic scenarios (all)", "full", ROOT, [PY, "harness/scenarios.py", "run", "--compare", "harness/scenarios-baseline.json",
                                                    "--out", os.path.join(os.environ.get("HARNESS_ARTIFACTS", tmp), "scenarios.json")], 0, r"compare: (\d+) of \1 scenarios identical"),
        ("worktrees.py mutation", "full", GRAPH, [PY, "-I", "mutate_worktrees.py", "--out", os.path.join(tmp, "mutants.json")], 0, r"unexpected survivors 0; stale allowlist entries 0"),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tier", nargs="?", default="standard", choices=TIERS)
    ap.add_argument("--only", nargs="+", metavar="STEP", help="run only steps whose name contains one of these strings")
    ap.add_argument("--list", action="store_true", help="list the steps of the tier and exit")
    ap.add_argument("--json", metavar="PATH", help="also write the results as JSON")
    a = ap.parse_args()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        chosen = [s for s in steps(tmp) if TIERS.index(s[1]) <= TIERS.index(a.tier)
                  and (not a.only or any(o.lower() in s[0].lower() for o in a.only))]
        if a.list:
            for name, tier, cwd, cmd, _, _ in chosen:
                print(f"{tier:9} {name:34} (cd {cwd.relative_to(ROOT) or '.'} && {' '.join(c.replace(tmp, '$TMP') for c in cmd[1:])})")
            return 0
        if not chosen:
            ap.error("no step matches --only")
        for name, tier, cwd, cmd, want, pattern in chosen:
            if sys.stdout.isatty():
                print(f"… {name}", end="", flush=True)
            t0 = time.time()
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=tmp))
            ok = r.returncode == want and (pattern is None or re.search(pattern, r.stdout, re.M) is not None)
            last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [""])[-1]
            results.append({"step": name, "tier": tier, "ok": ok, "exit": r.returncode, "seconds": round(time.time() - t0, 1), "summary": last[:160]})
            print(f"\r{'PASS' if ok else 'FAIL'}  {name:34} {results[-1]['seconds']:7.1f}s  {last[:90]}")
            if not ok:
                print("      " + "\n      ".join((r.stdout + r.stderr).strip().splitlines()[-25:]))
    failed = [r["step"] for r in results if not r["ok"]]
    print(f"\n{a.tier}: {len(results) - len(failed)} of {len(results)} steps passed" + (f"; failed: {', '.join(failed)}" if failed else ""))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"tier": a.tier, "ok": not failed, "steps": results}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
