#!/usr/bin/env python3
"""validate.py — validate a graph run record directory against graph-record.schema.json
plus the cross-file rules the schema lists under x-crossfile.

usage: validate.py RUN_DIR [--models haiku,sonnet,opus,fable] [--artifacts node=sha256,...]
exit 0: conforms. exit 1: findings (first finding on stdout line 1 as "<rule> <subject>: <message>"). exit 2: usage/parse error.
"""
import argparse
import re
import json
import os
import sys

import jsonschema
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["graph", "checks", "progress", "framing", "rules", "lessons"]


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate mapping keys instead of silently overwriting."""


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


def load(run_dir):
    rec = {}
    for name in FILES:
        p = os.path.join(run_dir, f"{name}.yaml")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                rec[name] = yaml.load(f, Loader=UniqueSafeLoader)
    return rec


def authored_proof_word(name, raw, data):
    """X12 permits literal provenance quotes, not authored claims or comments."""
    pattern = re.compile(r"\bproven\b", re.IGNORECASE)
    spans = []
    if name == "rules":
        tree = yaml.compose(raw, Loader=yaml.SafeLoader)
        tokens = [t for t in yaml.scan(raw) if isinstance(t, yaml.tokens.ScalarToken)]
        if isinstance(tree, yaml.MappingNode):
            for key, value in tree.value:
                if key.value != "rules" or not isinstance(value, yaml.SequenceNode):
                    continue
                for rule in value.value:
                    if not isinstance(rule, yaml.MappingNode):
                        continue
                    for field, quote in rule.value:
                        if field.value != "quote" or not isinstance(quote, yaml.ScalarNode):
                            continue
                        for token in tokens:
                            start, end = token.start_mark.index, token.end_mark.index
                            if quote.start_mark.index <= start and end <= quote.end_mark.index and token.value == quote.value:
                                # Anchor names and comments are outside scalar tokens.
                                # Block-scalar header comments are not quoted content.
                                if token.style in ("|", ">"):
                                    start = raw.find("\n", start, end) + 1
                                if start > 0:
                                    spans.append((start, end))
    masked = list(raw)
    for start, end in spans:
        masked[start:end] = " " * (end - start)
    if pattern.search("".join(masked)):
        return True

    def authored(value, path=()):
        if name == "rules" and len(path) == 3 and path[0] == "rules" and isinstance(path[1], int) and path[2] == "quote":
            return False
        if isinstance(value, str):
            return bool(pattern.search(value))
        if isinstance(value, dict):
            return any(authored(k) or authored(v, path + (k,)) for k, v in value.items())
        if isinstance(value, list):
            return any(authored(v, path + (i,)) for i, v in enumerate(value))
        return False

    # Decoded authored strings catch aliases/escapes referring to exempt text.
    return authored(data)


def schema_findings(rec, schema):
    v = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(v.iter_errors(rec), key=lambda e: tuple((type(p).__name__, str(p)) for p in e.absolute_path)):
        path = "/".join(str(p) for p in e.absolute_path) or "<root>"
        out.append(("SCHEMA", path, e.message))
    return out


def crossfile_findings(rec, models, artifacts, run_dir):
    f = []
    g = rec.get("graph", {}).get("nodes", [])
    rows = rec.get("checks", {}).get("rows", [])
    prog = rec.get("progress", {})
    fr = rec.get("framing", {})
    rules = {r["id"] for r in rec.get("rules", {}).get("rules", [])}
    ids = [n["id"] for n in g]
    for x in sorted(set(i for i in ids if ids.count(i) > 1)):
        f.append(("X22", "graph", f"duplicate node id {x}"))
    nodes = {n["id"]: n for n in g}
    ladder = {t: i for i, t in enumerate(models)} if models else None

    # X01
    for n in g:
        for c in n["checks"]:
            if not any(r["subject"].get("kind") == "node" and r["subject"].get("node") == n["id"] and r["subject"].get("check") == c["id"] and r["attempt"] == 1 for r in rows):
                f.append(("X01", n["id"], f"check {c['id']} has no attempt-1 row"))
    # X02 name-match; X15 DAG; X14 unique writes
    seen_writes = {}
    adj = {n: [] for n in ids}
    for n in g:
        for u in n["reads"]["upstream"]:
            if u["node"] not in nodes:
                f.append(("X02", n["id"], f"reads unknown node {u['node']}")); continue
            adj[u["node"]].append(n["id"])
            for s in u["sections"]:
                if s not in nodes[u["node"]]["shape"]:
                    f.append(("X02", n["id"], f"reads section '{s}' not in {u['node']}.shape"))
        for w in n["writes"]:
            if w in seen_writes:
                f.append(("X14", n["id"], f"writes {w} also written by {seen_writes[w]}"))
            seen_writes[w] = n["id"]
    state, order = {}, []
    def visit(x):
        if state.get(x) == 1: return True
        if state.get(x) == 2: return False
        state[x] = 1
        cyc = any(visit(y) for y in adj[x])
        state[x] = 2; order.append(x); return cyc
    if any(visit(x) for x in ids if x not in state):
        f.append(("X15", "graph", "reads graph has a cycle"))
    # X03
    risk_ids = {r["id"] for r in fr.get("risks", [])}
    for n in g:
        sr = n["split_reason"]
        if sr.get("risk") and sr["risk"] not in risk_ids:
            f.append(("X03", n["id"], f"split_reason.risk {sr['risk']} not in framing.risks"))
        for m in sr.get("nodes", []):
            if m not in nodes:
                f.append(("X03", n["id"], f"split_reason.nodes names unknown {m}"))
    # X04
    for r in fr.get("risks", []):
        gb = r["guarded_by"]
        if gb["kind"] == "gate":
            if gb["node"] not in nodes:
                f.append(("X04", r["id"], f"guarded_by node {gb['node']} unknown"))
            elif gb["check"] not in {c["id"] for c in nodes[gb["node"]]["checks"]}:
                f.append(("X04", r["id"], f"guarded_by check {gb['check']} not on {gb['node']}"))
    # X05, X06, X18
    subs = {s["id"]: s for s in prog.get("subagents", [])}
    for r in rows:
        sid = r["isolation"].get("subagent")
        if sid and sid not in subs:
            f.append(("X05", _subj(r), f"isolation subagent {sid} not in progress.subagents"))
    ea = prog.get("audits", {}).get("evidence", {}).get("isolation", {})
    if ea.get("subagent") and ea["subagent"] not in subs:
        f.append(("X05", "audits.evidence", f"subagent {ea['subagent']} not in progress.subagents"))
    for n in ids:
        roles = {}
        for s in prog.get("subagents", []):
            if s.get("node") == n:
                roles.setdefault(s["id"], set()).add(s["role"])
        for sid, rs in roles.items():
            if {"builder", "reviewer"} <= rs:
                f.append(("X06", n, f"subagent {sid} is both builder and reviewer"))
    for n in g:
        if all(c["type"] == "review" for c in n["checks"]):
            started = any(r["subject"].get("node") == n["id"] and r["isolation"]["kind"] != "not_run" for r in rows)
            if started and not any(s.get("node") == n["id"] and s["role"] == "reviewer" for s in subs.values()):
                f.append(("X18", n["id"], "review-only node has run but has no reviewer subagent in progress.subagents"))
    # X07, X08
    if ladder is None:
        if any(n.get("model") or n.get("reviewer_tier") for n in g):
            f.append(("X08", "run", "--models ladder required to check tiers (X07, X08)"))
    else:
        top = len(models) - 1
        for n in g:
            m = n.get("model")
            rt = n.get("reviewer_tier")
            if rt is not None and rt not in ladder:
                f.append(("X07", n["id"], f"reviewer_tier {rt} not on ladder"))
            if not m: continue
            if m["tier"] not in ladder:
                f.append(("X08", n["id"], f"tier {m['tier']} not on ladder"))
            else:
                want = min(len(m["tier_rule"]) + m["escalations"], top)
                if ladder[m["tier"]] != want:
                    f.append(("X08", n["id"], f"tier {m['tier']} (index {ladder[m['tier']]}) != rule index {want}"))
                if rt is not None and rt in ladder and ladder[rt] < ladder[m["tier"]]:
                    f.append(("X07", n["id"], f"reviewer_tier {rt} below builder tier {m['tier']}"))
    # X09
    for r in rows:
        for e in r.get("exercises", []):
            if e not in rules:
                f.append(("X09", _subj(r), f"exercises {e} not in rules"))
    # X10
    pg = prog.get("graph", {})
    listed = [x for k in ("accepted", "running", "failed", "blocked", "dissent", "escalated", "not_started") for x in pg.get(k, [])]
    if sorted(listed) != sorted(ids):
        f.append(("X10", "progress.graph", f"state lists {sorted(listed)} != node set {sorted(ids)}"))
    # X11
    for r in rows:
        ev = r["evidence"]
        if ev["kind"] == "carried":
            fn = ev["from_node"]
            src_node = nodes.get(fn)
            gate_check = (src_node.get("code") or {}).get("gate") if src_node else None
            # the carried check: ev.from_check when given; else code.gate; else the node's only check; else ambiguous
            if ev.get("from_check"):
                gate_check = ev["from_check"]
            elif gate_check is None and src_node and len(src_node["checks"]) == 1:
                gate_check = src_node["checks"][0]["id"]
            if gate_check is None:
                f.append(("X11", _subj(r), f"carried from {fn}, which has several checks: evidence.from_check must name the one carried"))
            if src_node and gate_check and gate_check not in {c["id"] for c in src_node["checks"]}:
                f.append(("X11", _subj(r), f"carried check {gate_check} is not a check of {fn}"))
            gate_rows = [x for x in rows if x["subject"].get("node") == fn and x["subject"].get("check") == gate_check]
            newest_gate = max(gate_rows, key=lambda x: x["attempt"]) if gate_rows else None
            if gate_check and (newest_gate is None or newest_gate["verdict"] != "pass"):
                f.append(("X11", _subj(r), f"carried from {fn} ({gate_check}) but its latest gate row is absent or not pass"))
            # the sha is checked on the newest carried row for this subject only: an earlier attempt's carry is history
            same_subject = [x for x in rows if x["subject"] == r["subject"] and x["evidence"].get("kind") == "carried"]
            is_newest = r["attempt"] == max(x["attempt"] for x in same_subject)
            if fn not in artifacts:
                if is_newest:
                    f.append(("X11", _subj(r), f"carried sha256 cannot be checked: no --artifacts entry for {fn}"))
            elif is_newest and artifacts[fn] != ev["sha256"]:
                f.append(("X11", _subj(r), "carried sha256 differs from artifact"))
    # X12
    for name in FILES:
        p = os.path.join(run_dir, f"{name}.yaml")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as source:
                raw = source.read()
            if authored_proof_word(name, raw, rec[name]):
                f.append(("X12", name, "contains authored 'proven' outside literal rules[*].quote source content"))
    # X13
    hyps = {(h["node"], h["before_attempt"]) for h in prog.get("hypotheses", [])}
    for r in rows:
        if r["attempt"] > 1:
            key = r["subject"].get("node") or r["subject"].get("item") or "integration"
            if (key, r["attempt"]) not in hyps:
                f.append(("X13", _subj(r), f"attempt {r['attempt']} has no hypothesis entry for {key}"))
    # X16
    latest = {}
    for r in rows:
        if r["subject"].get("node"):
            k = (r["subject"]["node"], r["subject"].get("check"))
            if k not in latest or r["attempt"] > latest[k]["attempt"]:
                latest[k] = r
    dis = sorted({k[0] for k, r in latest.items() if r["verdict"] == "dissent"})
    if dis != sorted(pg.get("dissent", [])):
        f.append(("X16", "progress.graph.dissent", f"{sorted(pg.get('dissent', []))} != latest-attempt dissent rows {dis}"))
    esc = {k[0] for k, r in latest.items() if r["verdict"] == "escalated"}
    if not esc <= set(pg.get("escalated", [])):
        f.append(("X16", "progress.graph.escalated", "escalated rows not all listed"))
    # X31: a directly contradictory accepted state is never valid.
    for (node, check), row in latest.items():
        if node in pg.get("accepted", []) and row["verdict"] in ("fail", "dissent", "escalated"):
            f.append(("X31", node, f"accepted with latest {check} verdict {row['verdict']}"))
    # X17
    e = prog.get("audits", {}).get("evidence", {})
    if e and e.get("miscited", 0) + e.get("unfound", 0) > e.get("rows", 0):
        f.append(("X17", "audits.evidence", "miscited + unfound exceeds rows"))
    if e and e.get("verdict") == "pass" and e.get("rows", 0) > 0 and e.get("isolation", {}).get("kind") != "fresh_subagent":
        f.append(("X17", "audits.evidence", "pass requires a fresh evidence auditor"))
    if e and e.get("verdict") in ("pass", "fail") and e.get("rows", 0) > 0:
        ratio = (e["miscited"] + e["unfound"]) / e["rows"]
        want = "pass" if ratio <= 0.10 else "fail"
        if e["verdict"] != want:
            f.append(("X17", "audits.evidence", f"verdict {e['verdict']} inconsistent with ratio {ratio:.2f}"))
    # X20
    for n in g:
        c = n.get("code")
        if c:
            chk = next((x for x in n["checks"] if x["id"] == c["gate"]), None)
            if chk is None:
                f.append(("X20", n["id"], f"code.gate {c['gate']} is not one of the node's checks"))
            elif chk["type"] != "exec":
                f.append(("X20", n["id"], f"code.gate {c['gate']} is not an exec check"))
    # X21 pass consistency
    for r in rows:
        if r["verdict"] != "pass": continue
        ev = r["evidence"]
        if ev["kind"] == "exec" and ev["actual_exit"] != ev["expected_exit"]:
            sj = r["subject"]; nd = nodes.get(sj.get("node"))
            partial = nd and any(c["id"] == sj.get("check") and c.get("exec_available") == "partial" for c in nd["checks"])
            if not partial:
                f.append(("X21", _subj(r), f"pass with actual_exit {ev['actual_exit']} != expected_exit {ev['expected_exit']}"))
        if ev["kind"] == "excerpt":
            secs = ev.get("sections", [])
            if not secs or any(x["verdict"] != "pass" for x in secs):
                f.append(("X21", _subj(r), "pass with a failing or empty sections list"))
    # X22 uniqueness
    def dupes(seq):
        seen, d = set(), []
        for x in seq:
            if x in seen: d.append(x)
            seen.add(x)
        return d
    for x in dupes([(json.dumps(r["subject"], sort_keys=True), r["attempt"]) for r in rows]):
        f.append(("X22", "checks", f"duplicate subject/attempt {x}"))
    for n in g:
        for x in dupes([c["id"] for c in n["checks"]]): f.append(("X22", n["id"], f"duplicate check id {x}"))
    for x in dupes([r["id"] for r in rec.get("rules", {}).get("rules", [])]): f.append(("X22", "rules", f"duplicate rule id {x}"))
    for x in dupes([o["id"] for o in prog.get("open_issues", [])]): f.append(("X22", "open_issues", f"duplicate issue id {x}"))
    for x in dupes([a["id"] for a in prog.get("assumptions", [])]): f.append(("X22", "progress.assumptions", f"duplicate id {x}"))
    fids = [a["id"] for a in fr.get("assumptions", [])] + [u["id"] for u in fr.get("unknowns", [])] + [r["id"] for r in fr.get("risks", [])]
    for x in dupes(fids): f.append(("X22", "framing", f"duplicate id {x} across assumptions/unknowns/risks"))
    for x in dupes([(s_["id"], s_["role"], s_.get("node")) for s_ in prog.get("subagents", [])]): f.append(("X22", "subagents", f"duplicate entry {x}"))
    # X23 references resolve
    issue_ids = {o["id"] for o in prog.get("open_issues", [])}
    for r in rows:
        sj = r["subject"]
        if sj["kind"] == "node":
            if sj["node"] not in nodes: f.append(("X23", _subj(r), f"subject.node {sj['node']} unknown"))
            else:
                cids = {c["id"] for c in nodes[sj["node"]]["checks"]}
                partial = {c["id"] + "-residue" for c in nodes[sj["node"]]["checks"] if c.get("exec_available") == "partial"}
                if sj["check"] not in cids | partial: f.append(("X23", _subj(r), f"subject.check {sj['check']} not on {sj['node']}"))
        fn = r["evidence"].get("from_node")
        if fn and fn not in nodes: f.append(("X23", _subj(r), f"evidence.from_node {fn} unknown"))
    for d in prog.get("decisions", []):
        if d.get("node") and d["node"] not in nodes: f.append(("X23", "decisions", f"node {d['node']} unknown"))
    items = {r["subject"].get("item") for r in rows if r["subject"]["kind"] == "acceptance"}
    for h in prog.get("hypotheses", []):
        if h["node"] not in nodes and h["node"] not in items and not (h["node"] == "integration" and any(r["subject"]["kind"] == "integration" for r in rows)): f.append(("X23", "hypotheses", f"node {h['node']} is neither a node nor an acceptance item"))
    for s_ in prog.get("subagents", []):
        if s_.get("node") and s_["node"] not in nodes: f.append(("X23", "subagents", f"node {s_['node']} unknown"))
    for e in rec.get("lessons", {}).get("entries", []):
        if e["node"] not in nodes: f.append(("X23", "lessons", f"node {e['node']} unknown"))
    na = prog.get("next_action", {})
    if "node" in na and na["node"] not in nodes: f.append(("X23", "next_action", f"node {na['node']} unknown"))
    if "issue" in na and na["issue"] not in issue_ids: f.append(("X23", "next_action", f"issue {na['issue']} not in open_issues"))
    # X24 produces ⊆ shape
    for n in g:
        for d in n["does"]:
            if d["produces"] not in n["shape"]: f.append(("X24", n["id"], f"does produces '{d['produces']}' not in shape"))
    # X25 tier_rule consistency (lines frozen at dispatch: a node with a check_revision decision is exempt)
    revised = {d.get("node") for d in prog.get("decisions", []) if d["kind"] == "check_revision"}
    for n in g:
        m = n.get("model")
        if not m or n["id"] in revised: continue
        fired = set(m["tier_rule"])
        want = set()
        if all(c["type"] == "review" for c in n["checks"]): want.add("review_only_check")
        if len(n["reads"]["upstream"]) >= 3: want.add("reads_three_or_more_upstream")
        if len(n["needs"]) >= 2: want.add("needs_two_or_more_domains")
        derivable = {"review_only_check", "reads_three_or_more_upstream", "needs_two_or_more_domains"}
        if (fired & derivable) != want:
            f.append(("X25", n["id"], f"tier_rule {sorted(fired & derivable)} inconsistent with node; expected {sorted(want)}"))
    # X27: progress references the framing assumption namespace, not risks/unknowns.
    assumption_ids = {item["id"] for item in fr.get("assumptions", [])}
    for item in prog.get("assumptions", []):
        if item["id"] not in assumption_ids:
            f.append(("X27", "progress.assumptions", f"assumption {item['id']} is absent from framing.assumptions"))
    # X28 partial exec checks: a non-matching exit needs a <id>-residue review row with its own red evidence
    for n in g:
        for c in n["checks"]:
            if c.get("exec_available") != "partial": continue
            for r in rows:
                sj = r["subject"]
                if sj.get("node") != n["id"] or sj.get("check") != c["id"]: continue
                ev = r["evidence"]
                if ev["kind"] == "exec" and ev["actual_exit"] != ev["expected_exit"]:
                    res = [x for x in rows if x["subject"].get("node") == n["id"] and x["subject"].get("check") == c["id"] + "-residue" and x["attempt"] == r["attempt"]]
                    if not res:
                        f.append(("X28", _subj(r), f"exec exit {ev['actual_exit']} != {ev['expected_exit']} with no {c['id']}-residue row for attempt {r['attempt']}"))
                    elif res[0]["verdict"] in ("pass", "fail") and (res[0]["type"] != "review" or res[0]["isolation"]["kind"] != "fresh_subagent" or res[0]["red_evidence"]["kind"] != "mutant"):
                        f.append(("X28", _subj(r), "a residue verdict needs a fresh review with mutant red evidence (an unresolved degraded row is allowed)"))
                    elif r["verdict"] != res[0]["verdict"]:
                        f.append(("X28", _subj(r), f"verdict {r['verdict']} differs from residue row verdict {res[0]['verdict']}"))
                    elif res[0]["red_evidence"]["kind"] == "not_run" and res[0]["verdict"] == "pass":
                        f.append(("X28", _subj(r), "residue row passes with no red evidence"))
    # X29 pending unknowns are tied to a live blocker
    na = prog.get("next_action", {})
    for u in fr.get("unknowns", []):
        if u.get("disposition") != "pending": continue
        if u.get("issue") not in issue_ids:
            f.append(("X29", f"unknown {u['id']}", f"pending but issue {u.get('issue')} not in open_issues"))
        elif not (na.get("kind") == "blocked" and na.get("issue") == u["issue"]):
            f.append(("X29", f"unknown {u['id']}", f"pending but next_action is not blocked on {u['issue']}"))
    # X30 reserve runs: at most ceil(limit/10) non-audit entries; each tied to a row; audits alone may take consumed past limit
    import math
    us = prog.get("usage", {})
    rr = us.get("reserve_runs", [])
    all_rows = rec.get("checks", {}).get("rows", [])
    if us.get("unit") == "node_runs":
        non_audit = [e for e in rr if e["kind"] != "audit"]
        cap = math.ceil(us.get("limit", 0) / 10)
        if len(non_audit) > cap:
            f.append(("X30", "usage.reserve_runs", f"{len(non_audit)} non-audit entries exceed ceil(limit/10) = {cap}"))
        audits_in = [e for e in rr if e["kind"] == "audit"]
        if us.get("consumed", 0) > us.get("limit", 0) + len(audits_in):
            f.append(("X30", "usage.consumed", f"{us.get('consumed')} exceeds limit {us.get('limit')} by more than the {len(audits_in)} audit run(s) recorded in reserve_runs"))
    row_keys = {(r["subject"].get("node"), r["attempt"]) for r in all_rows if r["subject"].get("kind") == "node"}
    integ_attempts = {r["attempt"] for r in all_rows if r["subject"].get("kind") in ("integration", "acceptance")}
    seen_audits = set()
    for e in rr:
        k = e["kind"]
        if k in ("correction_return", "re_gate"):
            if (e.get("node"), e.get("attempt")) not in row_keys:
                f.append(("X30", f"reserve run {e.get('node')}#{e.get('attempt')}", "no checks row for that node and attempt"))
        elif k == "integration":
            if e.get("attempt") not in integ_attempts:
                f.append(("X30", f"reserve run integration#{e.get('attempt')}", "no integration- or acceptance-subject row at that attempt"))
        elif k == "audit":
            if e.get("audit") in seen_audits:
                f.append(("X30", f"reserve run audit {e.get('audit')}", "listed more than once"))
            seen_audits.add(e.get("audit"))
    # X32 rule coverage: every deliverable rule is exercised by a checks row or listed as unchecked with a reason
    rule_ids = {r["id"]: r for r in rec.get("rules", {}).get("rules", [])}
    exercised = {x for r in rec.get("checks", {}).get("rows", []) if r["subject"].get("kind") == "acceptance" for x in (r.get("exercises") or [])}  # acceptance rows only (schema: exercises is an acceptance-row field; run 11 oi-r11-1)
    unchecked = {u["id"] for u in prog.get("unchecked_rules", [])}
    for uid in unchecked:
        if uid not in rule_ids:
            f.append(("X32", "progress.unchecked_rules", f"{uid} is not a rules id"))
        elif uid in exercised:
            f.append(("X32", "progress.unchecked_rules", f"{uid} is both exercised and listed as unchecked"))
    for rid, r in rule_ids.items():
        if "deliverable" in (r.get("concerns") or []) and rid not in exercised and rid not in unchecked:
            f.append(("X32", f"rules {rid}", "concerns the deliverable but no checks row exercises it and progress.unchecked_rules does not list it"))
    # X33 (v3.5.1, D66): an exec evidence command whose first `cd` names a relative path depends on the lead's working directory; the auditor cannot rerun it as written
    import re as _re
    for i, r in enumerate(rec.get("checks", {}).get("rows", [])):
        ev = r.get("evidence") or {}
        if ev.get("kind") == "exec" and isinstance(ev.get("command"), str):
            m = _re.search(r"(?:^|&&|;)\s*cd\s+(\S+)", ev["command"])
            if m and not m.group(1).startswith(("/", "~", "$")):
                f.append(("X33", f"checks row {i} evidence.command", f"cd {m.group(1)} is relative; cite an absolute path"))
    # X26 rows == 0
    e = prog.get("audits", {}).get("evidence", {})
    if e and e.get("rows", 0) == 0 and e.get("verdict") == "fail":
        f.append(("X26", "audits.evidence", "fail with zero rows"))
    # X19 — prose rules: report count only
    manual = [r for r in rec.get("rules", {}).get("rules", []) if set(r.get("concerns", [])) & {"graph", "checks", "progress"}]
    return f, len(manual)


def _subj(r):
    s = r["subject"]
    base = s.get("node") or s.get("item") or s["kind"]
    return f"{base}#{r['attempt']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--models", default="", help="comma-separated ladder, cheapest first")
    ap.add_argument("--artifacts", default="", help="node=sha256,... for X11")
    ap.add_argument("--all", action="store_true", help="print every finding, not only the first")
    a = ap.parse_args()
    try:
        with open(os.path.join(HERE, "graph-record.schema.json"), encoding="utf-8") as fh:
            schema = json.load(fh)
        rec = load(a.run_dir)
    except Exception as ex:  # noqa: BLE001
        print(f"usage: {ex}", file=sys.stderr); return 2
    models = [m.strip() for m in a.models.split(",")] if a.models else []
    if any(not m for m in models) or len(models) != len(set(models)):
        ap.error("--models must be a list of distinct nonempty runtime model IDs")
    artifacts = {}
    for kv in a.artifacts.split(",") if a.artifacts else []:
        parts = kv.split("=", 1)
        if len(parts) != 2 or not parts[0] or not re.fullmatch(r"[0-9a-f]{64}", parts[1]) or parts[0] in artifacts:
            ap.error("--artifacts must contain unique node=sha256 entries (64 lowercase hex digits)")
        artifacts[parts[0]] = parts[1]
    findings = schema_findings(rec, schema)
    if not findings:
        xf, manual = crossfile_findings(rec, models, artifacts, a.run_dir)
        findings += xf
    else:
        manual = None
        findings.append(("NOTE", "run", "cross-file rules not evaluated while schema findings exist"))
    if findings:
        for rule, subj, msg in (findings if a.all else findings[:1]):
            print(f"{rule} {subj}: {msg}")
        if not a.all and len(findings) > 1:
            print(f"... {len(findings) - 1} more (use --all)")
        return 1
    print(f"OK {a.run_dir}: schema + crossfile hold" + (f"; {manual} prose rule(s) in rules.yaml concern the record and need manual check" if manual else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
