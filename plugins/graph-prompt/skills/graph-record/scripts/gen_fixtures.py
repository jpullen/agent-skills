#!/usr/bin/env python3
"""gen_fixtures.py — schema-driven mutation fixtures for validate.py.

Starting from a valid record, generate one mutant per (leaf, operation):
  delete   — remove the leaf
  type     — replace with a value of the wrong JSON type
  enum     — replace an enumerated value with one outside the set (enum/const leaves only)
  dup      — for arrays of objects with an `id` field: duplicate the first element
For each mutant, derive the EXPECTED outcome from the schema alone:
  delete   → caught iff the leaf is in its parent's `required` (or a conditional then-required that fires for this record)
  type     → caught always (every leaf has a type)
  enum     → caught always
  dup      → caught iff the array is uniqueItems or the item has an `id` (X22)
Then run validate.py and compare. Mismatches are coverage gaps (expected caught, survived) or over-strictness (expected survive, caught).

usage: gen_fixtures.py BASE_DIR OUT_DIR [--models ...]
Writes OUT_DIR/<n>-<op>-<path>/ for every mutant, plus OUT_DIR/report.md.
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys

import jsonschema
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["graph", "checks", "progress", "framing", "rules", "lessons"]
WRONG_TYPE = {"string": 42, "integer": "x", "number": "x", "boolean": "x", "array": "x", "object": "x", "null": "x"}


def load(d):
    rec = {}
    for n in FILES:
        p = os.path.join(d, f"{n}.yaml")
        if os.path.exists(p):
            rec[n] = yaml.safe_load(open(p)) or {}
    return rec


def dump(rec, d):
    os.makedirs(d, exist_ok=True)
    for n, v in rec.items():
        with open(os.path.join(d, f"{n}.yaml"), "w") as f:
            yaml.safe_dump(v, f, sort_keys=False, allow_unicode=True)


def resolve(schema, node):
    while "$ref" in node:
        ref = node["$ref"].split("/")[1:]
        cur = schema
        for k in ref:
            cur = cur[k]
        node = {**cur, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


def walk(schema, node, inst, path, out, parent_schema=None, parent_inst=None, key=None):
    """Collect (path, leaf_schema, parent_schema, parent_inst, key) for every leaf and container in inst."""
    node = resolve(schema, node)
    out.append((path, node, parent_schema, parent_inst, key))
    t = node.get("type")
    if isinstance(t, list):
        t = [x for x in t if x != "null"][0] if inst is not None else t[0]
    if t == "object" and isinstance(inst, dict):
        props = node.get("properties", {})
        for k, v in inst.items():
            if k in props:
                walk(schema, props[k], v, path + [k], out, node, inst, k)
            elif isinstance(node.get("additionalProperties"), dict):
                walk(schema, node["additionalProperties"], v, path + [k], out, node, inst, k)
    elif t == "array" and isinstance(inst, list):
        items = node.get("items", {})
        for i, v in enumerate(inst):
            walk(schema, items, v, path + [i], out, node, inst, i)


_IF_CACHE = {}


def _compiled(schema, if_schema):
    key = json.dumps(if_schema, sort_keys=True)
    if key not in _IF_CACHE:
        _IF_CACHE[key] = jsonschema.Draft202012Validator({**if_schema, "$defs": schema["$defs"]})
    return _IF_CACHE[key]


def effective_required(schema, parent_schema, parent_inst):
    """required keys from the parent's `required` plus any allOf/if-then whose `if` matches parent_inst."""
    req = set(parent_schema.get("required", []))
    conds = list(parent_schema.get("allOf", []))
    if "if" in parent_schema:
        conds.append({"if": parent_schema["if"], "then": parent_schema.get("then", {})})
    for c in conds:
        c = resolve(schema, c)
        if "if" in c and _compiled(schema, c["if"]).is_valid(parent_inst):
            req |= set(resolve(schema, c.get("then", {})).get("required", []))
    return req


def set_path(rec, path, value, delete=False):
    cur = rec
    for k in path[:-1]:
        cur = cur[k]
    if delete:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--models", default="")
    args = ap.parse_args()
    base, out, models = args.base, args.out, args.models
    if os.path.exists(out):
        ap.error("output must be a new directory; existing output is never deleted")
    schema = json.load(open(os.path.join(HERE, "graph-record.schema.json")))
    rec0 = load(base)
    baseline = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), base] + (["--models", models] if models else []), capture_output=True, text=True)
    if baseline.returncode != 0:
        ap.error("baseline must validate before mutation: " + baseline.stdout + baseline.stderr)
    os.makedirs(out)
    leaves = []
    walk(schema, schema, rec0, [], leaves)
    mutants = []
    for path, node, pschema, pinst, key in leaves:
        if not path:
            continue
        t = node.get("type")
        if isinstance(t, list):
            t = t[0]
        # delete
        if isinstance(key, str):
            expect = key in effective_required(schema, pschema, pinst)
            mutants.append(("delete", path, None, True, expect))
        # type
        if t in WRONG_TYPE and "const" not in node:
            mutants.append(("type", path, WRONG_TYPE[t], False, True))
        # enum / const
        if "enum" in node or "const" in node:
            mutants.append(("enum", path, "zzz_not_a_value", False, True))
        # dup
        if t == "array" and isinstance(pinst.get(key) if isinstance(key, str) else None, list):
            arr = pinst[key]
            if arr and isinstance(arr[0], dict) and "id" in arr[0]:
                mutants.append(("dup", path, arr + [copy.deepcopy(arr[0])], False, True))
            elif arr and node.get("uniqueItems"):
                mutants.append(("dup", path, arr + [arr[0]], False, True))
    rows = []
    errors = []
    for n, (op, path, val, delete, expect) in enumerate(mutants, 1):
        rec = copy.deepcopy(rec0)
        try:
            set_path(rec, path, val, delete)
        except (KeyError, IndexError, TypeError):
            continue
        name = f"{n:03d}-{op}-{'.'.join(str(p) for p in path)}"[:120]
        d = os.path.join(out, name)
        dump(rec, d)
        r = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), d] + (["--models", models] if models else []), capture_output=True, text=True)
        if r.returncode not in (0, 1):
            errors.append((name, r.returncode, r.stderr[:200]))
        caught = r.returncode == 1
        first = r.stdout.splitlines()[0] if r.stdout else r.stderr.strip()[:80]
        rows.append((name, op, expect, caught, first))
    gaps = [r for r in rows if r[2] and not r[3]]
    strict = [r for r in rows if not r[2] and r[3]]
    with open(os.path.join(out, "report.md"), "w") as f:
        f.write(f"# gen_fixtures report\n\nbase: {base}\nmutants: {len(rows)}\n")
        f.write(f"expected caught: {sum(1 for r in rows if r[2])}; caught: {sum(1 for r in rows if r[3])}\n")
        f.write(f"gaps (expected caught, survived): {len(gaps)}\nover-strict (expected survive, caught): {len(strict)}\n\n")
        f.write("## gaps\n")
        for r in gaps:
            f.write(f"- {r[0]}\n")
        f.write("\n## over-strict\n")
        for r in strict:
            f.write(f"- {r[0]} → {r[4]}\n")
        f.write("\n## all\n| mutant | op | expect | caught | first finding |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r[0]} | {r[1]} | {'caught' if r[2] else 'survive'} | {'caught' if r[3] else 'survive'} | {r[4][:70]} |\n")
    print(f"mutants {len(rows)}; expected caught {sum(1 for r in rows if r[2])}; caught {sum(1 for r in rows if r[3])}; gaps {len(gaps)}; over-strict {len(strict)}")
    for error in errors:
        print("ERROR", error)
    for r in gaps:
        print("GAP", r[0])
    for r in strict:
        print("STRICT", r[0], "→", r[4][:60])

    return 1 if gaps or strict or errors else 0


if __name__ == "__main__":
    sys.exit(main())
