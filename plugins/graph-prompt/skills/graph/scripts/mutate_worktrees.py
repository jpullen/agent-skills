#!/usr/bin/env python3
"""mutate_worktrees.py — maintainer regression: single-site mutants of worktrees.py, each run against
test_worktrees.py in its own copy of the repository layout (run 13, T-49).

usage: python3 -I mutate_worktrees.py [SRC_DIR] [OUT_JSON]   (defaults: this directory, ./mutants.json)
Prints `mutants N killed K survived S`, then each survivor. The unmutated suite must pass in the harness
first, or the run stops. Run 13 classified 16 survivors as equivalent (message text, output order, a
display label, an unreachable defensive branch, and > vs >= where X35 makes equal attempts share a commit);
a new survivor outside that set is a test gap.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
src_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
out_json = sys.argv[2] if len(sys.argv) > 2 else "mutants.json"
text = open(os.path.join(src_dir, "worktrees.py")).read()
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
        mutants.append({"op": name, "line": line, "src": text[:i] + re.sub(rx, rep, text[i:], count=1)})
def run(mu):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
    d = os.path.join(root, "graph", "scripts"); os.makedirs(d)   # keep the repo layout the tests read (RF-63's test)
    shutil.copytree(os.path.join(src_dir, "..", "..", "graph-record", "scripts", "example-worktree"),
                    os.path.join(root, "graph-record", "scripts", "example-worktree"))
    for f in ("worktrees.py", "test_worktrees.py"):
        shutil.copy(os.path.join(src_dir, f), d)
    open(os.path.join(d, "worktrees.py"), "w").write(mu["src"])
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", d], capture_output=True, text=True, timeout=300)
    shutil.rmtree(root, ignore_errors=True)
    return {"op": mu["op"], "line": mu["line"], "killed": r.returncode != 0,
            "code": text.splitlines()[mu["line"] - 1].strip()}
base = run({"op": "baseline", "line": 1, "src": text})
if base["killed"]:
    sys.exit("baseline: the unmutated suite fails in the harness; no mutant result would mean anything")
with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(run, mutants))
json.dump(res, open(out_json, "w"), indent=1)
k = sum(r["killed"] for r in res)
print(f"mutants {len(res)} killed {k} survived {len(res) - k}")
for r in res:
    if not r["killed"]: print(f"SURVIVED {r['op']} L{r['line']}: {r['code']}")
