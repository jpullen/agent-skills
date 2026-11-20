#!/usr/bin/env python3
"""mutate_worktrees.py — mutation regression for worktrees.py (run 13, T-49; part of harness/run.py full).

Makes every single-site mutant of worktrees.py the operators below produce, and runs test_worktrees.py
against each in its own copy of the repository layout. A mutant the suite fails is killed. A survivor
must be listed in equivalent-mutants.json (operator, the source line, and why no test can tell it from
the original); any other survivor is a test gap. An allowlist entry no mutant matches any more is stale.

usage: python3 -I mutate_worktrees.py [--out JSON] [--jobs N] [--allow FILE]
Prints `mutants N killed K survived S; unexpected survivors U; stale allowlist entries T`, then each
unexpected survivor and stale entry. Exit 0 when U and T are 0, 1 otherwise, 2 if the unmutated suite
does not pass in the harness (no mutant result would mean anything; this happened once, see run 13).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--out"); ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
ap.add_argument("--allow", default=os.path.join(HERE, "equivalent-mutants.json"))
args = ap.parse_args()
text = open(os.path.join(HERE, "worktrees.py")).read()
lines = text.splitlines()
body_start = text.index('"""', text.index('"""') + 3) + 3   # skip the module docstring
OPS = [  # (name, regex, replacement)
    ("eq->ne", r" == ", " != "), ("ne->eq", r" != ", " == "),
    ("drop-not", r"\bif not ", "if "), ("add-not", r"\bif (?!not )", "if not "),
    ("ret0->1", r"return 0, ", "return 1, "), ("ret1if->0if", r"return \(1 if ", "return (0 if "),
    ("ret5->0", r"return 5, ", "return 0, "),
    ("fail3->2", r"Fail\(3, ", "Fail(2, "), ("fail4->3", r"Fail\(4, ", "Fail(3, "), ("fail2->3", r"Fail\(2, ", "Fail(3, "),
    ("sorted->list", r"\bsorted\(", "list("), ("ready0->-1", r"ready\[0\]", "ready[-1]"),
    ("gt->ge", r" > ", " >= "), ("lt->le", r" < ", " <= "),
    ("ffonly->ff", r'"--ff-only"', '"--ff"'), ("and->or", r" and ", " or "), ("or->and", r" or ", " and "),
    ("dotdot->dot", r'"\.\."', '"."'), ("in->notin", r" in (?=\()", " not in "),
]
mutants = []
for name, rx, rep in OPS:
    for m in re.finditer(rx, text[body_start:]):
        i = body_start + m.start()
        line = text.count("\n", 0, i) + 1
        mutants.append({"op": name, "line": line, "code": lines[line - 1].strip(), "src": text[:i] + re.sub(rx, rep, text[i:], count=1)})


def run(mu):
    root = tempfile.mkdtemp()
    d = os.path.join(root, "graph", "scripts"); os.makedirs(d)   # keep the layout the tests read
    shutil.copytree(os.path.join(HERE, "..", "..", "graph-record", "scripts", "example-worktree"),
                    os.path.join(root, "graph-record", "scripts", "example-worktree"))
    shutil.copy(os.path.join(HERE, "test_worktrees.py"), d)
    open(os.path.join(d, "worktrees.py"), "w").write(mu["src"])
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", d], capture_output=True, text=True, timeout=600)
    shutil.rmtree(root, ignore_errors=True)
    return {"op": mu["op"], "line": mu["line"], "code": mu["code"], "killed": r.returncode != 0}


if run({"op": "baseline", "line": 0, "code": "", "src": text})["killed"]:
    print("baseline: the unmutated suite fails in the harness"); sys.exit(2)
with ThreadPoolExecutor(args.jobs) as ex:
    res = list(ex.map(run, mutants))
allow = json.load(open(args.allow)) if os.path.exists(args.allow) else []
allowed = {(e["op"], e["code"]) for e in allow}
survivors = [r for r in res if not r["killed"]]
unexpected = [r for r in survivors if (r["op"], r["code"]) not in allowed]
stale = [e for e in allow if (e["op"], e["code"]) not in {(r["op"], r["code"]) for r in survivors}]
if args.out:
    json.dump(res, open(args.out, "w"), indent=1)
print(f"mutants {len(res)} killed {len(res) - len(survivors)} survived {len(survivors)}; unexpected survivors {len(unexpected)}; stale allowlist entries {len(stale)}")
for r in unexpected:
    print(f"SURVIVED {r['op']} L{r['line']}: {r['code']}")
for e in stale:
    print(f"STALE {e['op']}: {e['code']}")
sys.exit(1 if unexpected or stale else 0)
