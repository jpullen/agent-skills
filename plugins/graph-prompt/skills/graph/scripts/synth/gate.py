#!/usr/bin/env python3
"""Synthetic node gate (run machinery; copied into RUN_DIR/code by the engine). usage: gate.py NODE, cwd = the node's tree.

Every node n writes out/<n>.txt whose first line is v(n) = sha256(n | v(u) for u in sorted reads)[:16]; later lines must
start with "# ". A loose node's own line need only be 16 hex digits. Exit 1 with `UPSTREAM <u>` when a node it reads is
wrong (the evidence a lead reads as cause b), with `OWN missing` or `OWN wrong` otherwise; exit 0 with `ok`."""
import hashlib, json, os, re, sys

SPEC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec.json")))
_memo = {}


def v(n):
    if n not in _memo:
        _memo[n] = hashlib.sha256((n + "|" + "|".join(v(u) for u in sorted(SPEC["nodes"][n]))).encode()).hexdigest()[:16]
    return _memo[n]


def own_ok(n, text, loose):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if not lines:
        return False
    head = re.fullmatch(r"[0-9a-f]{16}", lines[0]) if loose else lines[0] == v(n)
    return bool(head) and all(l.startswith("# ") for l in lines[1:])


def first_line(path):
    try:
        return open(path).read().split("\n")[0]
    except (FileNotFoundError, IsADirectoryError):
        return None


def check(n, tree=".", strict=False):
    for u in sorted(SPEC["nodes"][n]):
        if first_line(os.path.join(tree, "out", f"{u}.txt")) != v(u):
            return 1, f"UPSTREAM {u}"
    try:
        text = open(os.path.join(tree, "out", f"{n}.txt")).read()
    except FileNotFoundError:
        return 1, "OWN missing"
    if not own_ok(n, text, n in SPEC["loose"] and not strict):
        return 1, "OWN wrong"
    return 0, "ok"


if __name__ == "__main__":
    if SPEC.get("byproduct"):   # a gate that leaves a cache behind, as pytest's __pycache__ does (RF-61)
        open("gate-cache.log", "a").write(sys.argv[1] + "\n")
    code, msg = check(sys.argv[1])
    print(msg)
    sys.exit(code)
