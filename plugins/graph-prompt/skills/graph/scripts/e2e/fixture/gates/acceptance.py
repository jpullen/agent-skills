#!/usr/bin/env python3
"""Acceptance items k1-k4 against the tree given as argv[1]. Prints `<item> pass|fail` per item;
exits non-zero if any fails. Run machinery of the e2e fixture (lives under RUN_DIR/code in a run)."""
import os, re, subprocess, sys

tree, here = os.path.abspath(sys.argv[1]), os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def cli(*a):
    return subprocess.run([sys.executable, "cli.py", *a], cwd=tree, capture_output=True, text=True, env=env)


def k1(): r = cli("5", "km", "m"); return r.returncode == 0 and r.stdout == "5000\n"
def k2(): r = cli("1", "mi", "ft"); return r.returncode == 0 and r.stdout == "5280\n"
def k3(): r = cli("1", "parsec", "m"); return r.returncode == 1 and r.stderr.strip() == "unknown unit: parsec"


def k4():
    tests = [os.path.join(here, f"test_{n}.py") for n in ("table", "parse", "cli")]
    if subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=tree, capture_output=True, env=env).returncode:
        return False
    srcs = [os.path.join(tree, "cli.py")] + [os.path.join(tree, "units", f) for f in os.listdir(os.path.join(tree, "units")) if f.endswith(".py")]
    return not any(re.search(r"^\s*(import|from)\s+(numpy|pint|requests)", open(p).read(), re.M) for p in srcs)


fail = 0
for name, fn in (("k1", k1), ("k2", k2), ("k3", k3), ("k4", k4)):
    try:
        ok = fn()
    except Exception:  # a missing cli.py or units/ is a fail, not a crash
        ok = False
    print(name, "pass" if ok else "fail")
    fail |= not ok
sys.exit(fail)
