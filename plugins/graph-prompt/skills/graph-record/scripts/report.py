#!/usr/bin/env python3
"""report.py: delivery-report generator for a graph run record, to the contract REPORT-SPEC.md.

Usage: report.py RUN_DIR [--markdown]

Reads rules.yaml, checks.yaml, progress.yaml and framing.yaml from RUN_DIR (read-only) and prints the
delivery report: what was checked, what passed (with the evidence kind), what failed (with an excerpt),
what is unresolved, dissent, escalations, unchecked rules, assumptions, both audits and usage, then a
final `status:` line. Exit 0 when the record meets the Definition of Done (status: complete), 1 when it
does not (status: partial; the report is still printed), 2 on usage or parse error.
The report states what the record says; it does not re-run any check or re-verify any evidence.
Python 3 standard library plus PyYAML only, plus coverage.py from this directory.
"""
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coverage import ParseError, UniqueSafeLoader, analyse, load_record  # noqa: E402

USAGE = "usage: report.py RUN_DIR [--markdown]"
HEADINGS = ("Checked", "Passed", "Failed", "Unresolved", "Dissent", "Escalated",
            "Unchecked rules", "Assumptions", "Audits", "Usage")
VERDICTS = ("pass", "fail", "unresolved", "void", "dissent", "escalated")
GRAPH_LISTS = ("running", "failed", "blocked", "dissent", "escalated", "not_started")


def one_line(text):
    if text is None:
        return ""
    return str(text).replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")


def cell(text):
    return one_line(text).replace("|", "\\|")


def need(cond, msg):
    if not cond:
        raise ParseError(msg)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def get(d, *path):
    for p in path:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


def load_framing(run_dir):
    path = os.path.join(run_dir, "framing.yaml")
    if not os.path.isfile(path):
        raise ParseError(f"framing.yaml is missing from {run_dir}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            framing = yaml.load(fh, Loader=UniqueSafeLoader)
    except (yaml.YAMLError, ValueError, UnicodeDecodeError) as ex:
        raise ParseError(f"framing.yaml: {' '.join(str(ex).split())}")
    need(isinstance(framing, dict) and isinstance(framing.get("assumptions"), list)
         and all(isinstance(a, dict) for a in framing["assumptions"]),
         "framing.yaml: `assumptions` must be a list of entries")
    return framing


def check_required(rows, prog):
    for i, r in enumerate(rows):
        s = r.get("subject")
        need(isinstance(s, dict), f"checks.yaml row {i}: `subject` must be a mapping")
        kind = s.get("kind")
        need(kind in ("node", "acceptance", "integration"), f"checks.yaml row {i}: subject.kind is not node, acceptance or integration")
        if kind == "node":
            need(isinstance(s.get("node"), str) and isinstance(s.get("check"), str),
                 f"checks.yaml row {i}: a node subject needs `node` and `check`")
        if kind == "acceptance":
            need(isinstance(s.get("item"), str), f"checks.yaml row {i}: an acceptance subject needs `item`")
        need(is_int(r.get("attempt")), f"checks.yaml row {i}: `attempt` must be an integer")
        need(r.get("verdict") in VERDICTS, f"checks.yaml row {i}: `verdict` is not in the verdict vocabulary")
    graph = prog.get("graph")
    need(isinstance(graph, dict), "progress.yaml: `graph` must be a mapping")
    for k in GRAPH_LISTS:
        need(isinstance(graph.get(k), list), f"progress.yaml: graph.{k} must be a list")
    need(is_int(get(prog, "audits", "wellformed", "exit_code")), "progress.yaml: audits.wellformed.exit_code must be an integer")
    ev = get(prog, "audits", "evidence")
    need(isinstance(ev, dict), "progress.yaml: audits.evidence must be a mapping")
    for k in ("rows", "miscited", "unfound"):
        need(is_int(ev.get(k)), f"progress.yaml: audits.evidence.{k} must be an integer")
    need(isinstance(ev.get("verdict"), str), "progress.yaml: audits.evidence.verdict must be a string")
    need(isinstance(ev.get("notes"), list), "progress.yaml: audits.evidence.notes must be a list")
    need(isinstance(get(prog, "next_action", "kind"), str), "progress.yaml: next_action.kind must be a string")
    need(isinstance(prog.get("assumptions"), list) and all(isinstance(a, dict) for a in prog["assumptions"]),
         "progress.yaml: `assumptions` must be a list of entries")


def subject_text(s):
    if s["kind"] == "node":
        return f"node:{s['node']}/{s['check']}"
    if s["kind"] == "acceptance":
        return f"acceptance:{s['item']}"
    return "integration"


def subject_key(s):
    if s["kind"] == "node":
        return ("node", s["node"], s["check"])
    if s["kind"] == "acceptance":
        return ("acceptance", s["item"])
    return ("integration",)


def latest_rows(rows):
    """Subjects in order of first appearance, each with its latest row (ties: the later row)."""
    order, latest = [], {}
    for r in rows:
        k = subject_key(r["subject"])
        if k not in latest:
            order.append(k)
            latest[k] = r
        elif r["attempt"] >= latest[k]["attempt"]:
            latest[k] = r
    return [latest[k] for k in order]


def sections_of(row):
    secs = get(row, "evidence", "sections")
    return [s for s in secs if isinstance(s, dict)] if isinstance(secs, list) else []


def failed_excerpt(row):
    for s in sections_of(row):
        if s.get("verdict") == "fail":
            return one_line(s.get("excerpt"))[:100]
    return ""


def dissent_positions(row):
    d = row.get("dissent")
    d = d if isinstance(d, dict) else {}
    first = ""
    for s in sections_of(row):
        if s.get("section") == d.get("section"):
            first = one_line(s.get("excerpt"))
            break
    return first, one_line(d.get("reviewer_excerpt"))


def build(run_dir):
    """Return (sections, status); sections is a list of (heading, count, columns, item rows, extra)."""
    rules, rows, prog = load_record(run_dir)
    framing = load_framing(run_dir)
    check_required(rows, prog)
    deliverable, _manual, _findings, _ok = analyse(rules, rows, prog)

    lat = latest_rows(rows)
    by = {v: [r for r in lat if r["verdict"] == v] for v in VERDICTS}
    by["unresolved"] = [r for r in lat if r["verdict"] in ("unresolved", "void")]

    def plain(rs):
        return [[subject_text(r["subject"]), str(r["attempt"])] for r in rs]

    secs = []
    secs.append(("Checked", ["Subject", "Attempt"], plain(lat)))
    secs.append(("Passed", ["Subject", "Attempt", "Evidence"],
                 [p + [one_line(get(r, "evidence", "kind"))] for p, r in zip(plain(by["pass"]), by["pass"])]))
    secs.append(("Failed", ["Subject", "Attempt", "Excerpt"],
                 [p + [failed_excerpt(r)] for p, r in zip(plain(by["fail"]), by["fail"])]))
    secs.append(("Unresolved", ["Subject", "Attempt"], plain(by["unresolved"])))
    secs.append(("Dissent", ["Subject", "Attempt", "Position", "Dissent"],
                 [p + list(dissent_positions(r)) for p, r in zip(plain(by["dissent"]), by["dissent"])]))
    secs.append(("Escalated", ["Subject", "Attempt"], plain(by["escalated"])))

    unchecked = []
    for rid, bucket, detail in deliverable:
        if bucket == "unchecked":
            unchecked.append([str(rid), "unchecked", one_line(detail)])
        elif bucket == "uncovered":
            unchecked.append([str(rid), "uncovered", ""])
    secs.append(("Unchecked rules", ["Rule", "Bucket", "Reason"], unchecked))

    assumptions = [["framing", one_line(a.get("id")), one_line(a.get("text"))] for a in framing["assumptions"]]
    assumptions += [["progress", one_line(a.get("id")), one_line(a.get("assumed"))] for a in prog["assumptions"]]
    secs.append(("Assumptions", ["Source", "Id", "Text"], assumptions))

    ev = prog["audits"]["evidence"]
    audit_pairs = [("note", one_line(n)) for n in ev["notes"]]
    audit_pairs += [("evidence rows", str(ev["rows"])), ("evidence miscited", str(ev["miscited"])),
                    ("evidence unfound", str(ev["unfound"])), ("evidence verdict", one_line(ev["verdict"])),
                    ("wellformed exit code", str(prog["audits"]["wellformed"]["exit_code"]))]
    usage = prog.get("usage") if isinstance(prog.get("usage"), dict) else {}
    usage_pairs = [(k, one_line(usage.get(k))) for k in ("consumed", "limit", "unit")]
    reserve = usage.get("reserve_runs")
    reserve = reserve if isinstance(reserve, list) else []
    for e in reserve:
        e = e if isinstance(e, dict) else {}
        text = one_line(e.get("kind"))
        for field, label in (("node", "node"), ("attempt", "attempt"), ("audit", "audit")):
            if e.get(field) is not None:
                text += f" {label}={one_line(e[field])}"
        usage_pairs.append(("reserve", text))

    counts = {h: len(items) for h, _c, items in secs}
    counts["Audits"] = len(ev["notes"])
    counts["Usage"] = len(reserve)

    complete = (
        all(not prog["graph"][k] for k in GRAPH_LISTS)
        and len(by["pass"]) == len(lat)
        and prog["audits"]["wellformed"]["exit_code"] == 0 and ev["verdict"] == "pass"
        and prog["next_action"]["kind"] == "delivery"
    )
    return secs, counts, audit_pairs, usage_pairs, ("complete" if complete else "partial")


def render(secs, counts, audit_pairs, usage_pairs, status, markdown):
    blocks = []
    tables = {h: (cols, items) for h, cols, items in secs}
    tables["Audits"] = (["Item", "Value"], [list(p) for p in audit_pairs])
    tables["Usage"] = (["Item", "Value"], [list(p) for p in usage_pairs])
    for h in HEADINGS:
        cols, items = tables[h]
        lines = [f"## {h}", f"count: {counts[h]}"]
        always = h in ("Audits", "Usage")
        if markdown:
            if items and (counts[h] > 0 or always):
                lines.append("| " + " | ".join(cols) + " |")
                lines.append("| " + " | ".join("---" for _ in cols) + " |")
                for it in items:
                    lines.append("| " + " | ".join(cell(c) for c in it) + " |")
        else:
            for it in items:
                if h in ("Checked", "Unresolved", "Escalated"):
                    lines.append(f"{it[0]} #{it[1]}")
                elif h in ("Passed", "Failed"):
                    lines.append(f"{it[0]} #{it[1]} | {it[2]}")
                elif h == "Dissent":
                    lines.append(f"{it[0]} #{it[1]} | {it[2]} | {it[3]}")
                elif h == "Unchecked rules":
                    lines.append("\t".join(it[:2] if it[1] == "uncovered" else it))
                elif h == "Assumptions":
                    lines.append(f"{it[0]} {it[1]}: {it[2]}")
                else:
                    lines.append(f"{it[0]}: {it[1]}")
        blocks.append("\n".join(lines))
    blocks.append(f"status: {status}")
    return "\n\n".join(blocks) + "\n"


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
        secs, counts, audit_pairs, usage_pairs, status = build(run_dir)
        text = render(secs, counts, audit_pairs, usage_pairs, status, markdown)
    except ParseError as ex:
        print(f"usage: {ex}", file=sys.stderr)
        return 2
    except Exception as ex:  # a record coverage.py cannot analyse is a parse error here (C4)
        print(f"usage: cannot analyse {run_dir}: {type(ex).__name__}: {' '.join(str(ex).split())}", file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
