#!/usr/bin/env python3
"""coverage.py: rule-coverage reporter for a graph run record, to the contract COVERAGE-SPEC.md.

Usage: coverage.py RUN_DIR [--markdown]

Reads rules.yaml, checks.yaml and progress.yaml from RUN_DIR (read-only) and reports, for every rule
that concerns the deliverable, whether an acceptance row exercises it, whether progress.unchecked_rules
lists it with a reason, or neither. Exit 0 when X32 holds, 1 when it does not, 2 on usage or parse error.
Python 3 standard library plus PyYAML only.
"""
import os
import sys

import yaml

USAGE = "usage: coverage.py RUN_DIR [--markdown]"
FILES = ("rules", "checks", "progress")


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently overwriting (as validate.py's loader does)."""


def _unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


class ParseError(Exception):
    pass


def load_record(run_dir):
    rec = {}
    for name in FILES:
        path = os.path.join(run_dir, f"{name}.yaml")
        if not os.path.isfile(path):
            raise ParseError(f"{name}.yaml is missing from {run_dir}")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec[name] = yaml.load(fh, Loader=UniqueSafeLoader)
        except (yaml.YAMLError, ValueError, UnicodeDecodeError) as ex:
            raise ParseError(f"{name}.yaml: {' '.join(str(ex).split())}")
    rules = rec["rules"]
    if not isinstance(rules, dict) or not isinstance(rules.get("rules"), list) \
            or not all(isinstance(r, dict) and "id" in r for r in rules["rules"]):
        raise ParseError("rules.yaml: `rules` must be a list of rule entries")
    checks = rec["checks"]
    if not isinstance(checks, dict) or not isinstance(checks.get("rows"), list) \
            or not all(isinstance(r, dict) for r in checks["rows"]):
        raise ParseError("checks.yaml: `rows` must be a list of rows")
    prog = rec["progress"]
    if not isinstance(prog, dict):
        raise ParseError("progress.yaml: top level must be a mapping")
    unchecked = prog.get("unchecked_rules")
    if unchecked is not None and (not isinstance(unchecked, list)
                                  or not all(isinstance(u, dict) and "id" in u for u in unchecked)):
        raise ParseError("progress.yaml: `unchecked_rules` must be a list of entries with `id` and `reason`")
    return rules["rules"], checks["rows"], prog


def one_line(text):
    return " ".join(str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")) if text is not None else ""


def analyse(rules, rows, prog):
    """Return (deliverable bucket list, manual list, findings, X32 holds)."""
    rule_ids = []
    seen = set()
    for r in rules:
        if r["id"] not in seen:
            seen.add(r["id"])
            rule_ids.append(r["id"])
    by_id = {}
    for r in rules:
        by_id.setdefault(r["id"], r)

    # acceptance rows only (C9); newest row per item (C20)
    acceptance = [r for r in rows
                  if isinstance(r.get("subject"), dict) and r["subject"].get("kind") == "acceptance"]
    item_order = []
    newest = {}
    for r in acceptance:
        item = r["subject"].get("item")
        if item not in newest:
            item_order.append(item)
            newest[item] = r
        elif _attempt(r) > _attempt(newest[item]):
            newest[item] = r
    exercisers = {}  # rule id -> items, by first appearance in checks.yaml
    for r in acceptance:
        item = r["subject"].get("item")
        for e in (r.get("exercises") or []):
            lst = exercisers.setdefault(e, [])
            if item not in lst:
                lst.append(item)
    for lst in exercisers.values():
        lst.sort(key=item_order.index)

    unchecked = {}
    for u in prog.get("unchecked_rules") or []:
        unchecked.setdefault(u["id"], u.get("reason"))

    deliverable, manual = [], []
    for rid in rule_ids:
        concerns = by_id[rid].get("concerns") or []
        if "deliverable" in concerns:
            if rid in exercisers:
                detail = ",".join(
                    "{}#{}={}".format(i, newest[i].get("attempt"), newest[i].get("verdict"))
                    for i in exercisers[rid])
                deliverable.append((rid, "exercised", detail))
            elif rid in unchecked:
                deliverable.append((rid, "unchecked", one_line(unchecked[rid])))
            else:
                deliverable.append((rid, "uncovered", ""))
        else:
            manual.append((rid, concerns))

    findings = []
    ok = True
    for rid, bucket, _ in deliverable:
        if bucket == "uncovered":
            ok = False
            findings.append(f"X32 rules {rid}: concerns the deliverable but no checks row exercises it "
                            "and progress.unchecked_rules does not list it")
    for uid in unchecked:
        if uid not in by_id:
            ok = False
            findings.append(f"X32 progress.unchecked_rules: {uid} is not a rules id")
        elif uid in exercisers:
            ok = False
            findings.append(f"X32 progress.unchecked_rules: {uid} is both exercised and listed as unchecked")
    for r in acceptance:
        for e in (r.get("exercises") or []):
            if e not in by_id:
                findings.append(f"X09 {r['subject'].get('item')}#{r.get('attempt')}: exercises {e} not in rules")
    return deliverable, manual, findings, ok


def _attempt(row):
    a = row.get("attempt")
    return a if isinstance(a, (int, float)) and not isinstance(a, bool) else 0


def render(deliverable, manual, findings, markdown):
    out = []
    if markdown:
        out.append("| Rule | Bucket | Detail |")
        out.append("| --- | --- | --- |")
        for rid, bucket, detail in deliverable:
            cell = detail.replace("|", "\\|")
            out.append(f"| {rid} | {bucket} | {cell} |" if cell else f"| {rid} | {bucket} | |")
    else:
        for rid, bucket, detail in deliverable:
            out.append(f"{rid}\t{bucket}\t{detail}" if bucket != "uncovered" else f"{rid}\t{bucket}")
    counts = {b: sum(1 for _, x, _ in deliverable if x == b) for b in ("exercised", "unchecked", "uncovered")}
    out.append("summary: exercised={exercised} unchecked={unchecked} uncovered={uncovered}".format(**counts))
    out.extend(findings)
    if manual:
        out.append("manual (not counted in the summary):")
        for rid, concerns in manual:
            out.append(f"  {rid} {','.join(str(c) for c in concerns)}")
    return "\n".join(out) + "\n"


def main(argv):
    markdown = False
    dirs = []
    for arg in argv:
        if arg == "--markdown":
            markdown = True
        elif arg.startswith("-") and arg != "-":
            print(USAGE + f" (unknown option {arg})", file=sys.stderr)
            return 2
        else:
            dirs.append(arg)
    if len(dirs) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    run_dir = dirs[0]
    if not os.path.isdir(run_dir):
        print(f"{USAGE} ({run_dir} is not a directory)", file=sys.stderr)
        return 2
    try:
        rules, rows, prog = load_record(run_dir)
    except ParseError as ex:
        print(f"usage: {ex}", file=sys.stderr)
        return 2
    deliverable, manual, findings, ok = analyse(rules, rows, prog)
    sys.stdout.write(render(deliverable, manual, findings, markdown))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
