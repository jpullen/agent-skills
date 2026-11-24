#!/usr/bin/env python3
"""Synthetic acceptance (run machinery). usage: accept.py TREE. k1: every node's file is right, loose nodes held to the
strict value; k2 (absence check): no file in TREE outside .git contains SECRET. Prints `<item> pass|fail`; exit 1 if any fails."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

tree = sys.argv[1]
k1 = all(gate.check(n, tree, strict=True)[0] == 0 for n in gate.SPEC["nodes"])
k2 = True
for root, dirs, files in os.walk(tree):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        try:
            if "SECRET" in open(os.path.join(root, f), errors="replace").read():
                k2 = False
        except OSError:
            pass
print("k1", "pass" if k1 else "fail")
print("k2", "pass" if k2 else "fail")
sys.exit(0 if k1 and k2 else 1)
