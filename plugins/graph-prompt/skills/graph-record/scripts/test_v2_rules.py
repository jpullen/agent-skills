"""Targeted tests for schema v2 rules D34–D36 (X21/X23/X25/X28, phase, exec_available). Run: python -m pytest -q test_v2_rules.py"""
import copy, os, pathlib, shutil, subprocess, sys
import yaml

HERE = pathlib.Path(__file__).parent
EXAMPLE = HERE / "example"
MODELS = "haiku,sonnet,opus,fable"


def load():
    return {f: yaml.safe_load((EXAMPLE / f"{f}.yaml").read_text()) for f in ["graph", "checks", "progress", "framing", "rules", "lessons"]}


def run(rec, tmp):
    d = tmp / "rec"
    if d.exists(): shutil.rmtree(d)
    d.mkdir()
    for k, v in rec.items():
        (d / f"{k}.yaml").write_text(yaml.safe_dump(v, sort_keys=False))
    r = subprocess.run([sys.executable, str(HERE / "validate.py"), str(d), "--models", MODELS, "--all"], capture_output=True, text=True)
    return r.returncode, r.stdout


def g1(rec):
    return next(n for n in rec["graph"]["nodes"] if n["id"] == "g1")


def test_example_holds(tmp_path):
    assert run(load(), tmp_path)[0] == 0


# D36 exec_available ------------------------------------------------------------

def test_exec_available_required(tmp_path):
    rec = load(); del g1(rec)["checks"][0]["exec_available"]
    code, out = run(rec, tmp_path); assert code == 1 and "exec_available" in out

def test_partial_requires_residue(tmp_path):
    rec = load(); g1(rec)["checks"][0]["exec_available"] = "partial"
    code, out = run(rec, tmp_path); assert code == 1 and "residue" in out

def test_yes_must_be_exec_type(tmp_path):
    rec = load(); n = next(x for x in rec["graph"]["nodes"] if x["id"] == "g3"); n["checks"][0]["exec_available"] = "yes"
    code, out = run(rec, tmp_path); assert code == 1

def test_program_considered_rejected(tmp_path):
    rec = load(); g1(rec)["rules"]["program_considered"] = "x"
    code, out = run(rec, tmp_path); assert code == 1 and "program_considered" in out


# D35 phase ---------------------------------------------------------------------

def test_reviewer_with_phase_needs_no_node(tmp_path):
    rec = load(); rec["progress"]["subagents"].append({"id": "a" + "0" * 16, "role": "reviewer", "phase": "integration", "tier": "opus"})
    assert run(rec, tmp_path)[0] == 0

def test_reviewer_without_phase_or_node_fails(tmp_path):
    rec = load(); rec["progress"]["subagents"].append({"id": "a" + "0" * 16, "role": "reviewer", "tier": "opus"})
    assert run(rec, tmp_path)[0] == 1

def test_phase_and_node_together_fails(tmp_path):
    rec = load(); rec["progress"]["subagents"].append({"id": "a" + "0" * 16, "role": "reviewer", "phase": "integration", "node": "g1", "tier": "opus"})
    assert run(rec, tmp_path)[0] == 1

def test_builder_cannot_have_phase(tmp_path):
    rec = load(); rec["progress"]["subagents"].append({"id": "a" + "0" * 16, "role": "builder", "phase": "integration", "tier": "opus"})
    assert run(rec, tmp_path)[0] == 1

def test_decision_with_phase(tmp_path):
    rec = load(); rec["progress"]["decisions"].append({"kind": "check_revision", "phase": "integration", "was": "a", "now": "b", "reason": "c"})
    assert run(rec, tmp_path)[0] == 0


# D34 frozen tier lines -------------------------------------------------------------

def test_x25_fires_without_revision(tmp_path):
    rec = load(); n = g1(rec); n["model"]["tier_rule"] = ["review_only_check"] + n["model"]["tier_rule"]
    n["model"]["tier"] = MODELS.split(",")[len(n["model"]["tier_rule"]) + n["model"]["escalations"]]
    code, out = run(rec, tmp_path); assert code == 1 and "X25" in out

def test_x25_exempt_with_check_revision(tmp_path):
    rec = load(); n = g1(rec); n["model"]["tier_rule"] = ["review_only_check"] + n["model"]["tier_rule"]
    n["model"]["tier"] = MODELS.split(",")[len(n["model"]["tier_rule"]) + n["model"]["escalations"]]
    rec["progress"]["decisions"].append({"kind": "check_revision", "node": "g1", "was": "review", "now": "exec", "reason": "structural"})
    code, out = run(rec, tmp_path); assert code == 0, out


# X28 residue rows --------------------------------------------------------------------

def _partial(rec):
    n = g1(rec); c = n["checks"][0]; c["exec_available"] = "partial"; c["residue"] = "fresh reviewer against the check text"
    row = next(r for r in rec["checks"]["rows"] if r["subject"].get("node") == "g1" and r["subject"].get("check") == c["id"])
    row["evidence"]["actual_exit"] = 1
    return c, row

def test_partial_exit_mismatch_needs_residue_row(tmp_path):
    rec = load(); _partial(rec)
    code, out = run(rec, tmp_path); assert code == 1 and "X28" in out

def test_partial_with_residue_row_passes(tmp_path):
    rec = load(); c, row = _partial(rec)
    rec["checks"]["rows"].append({"subject": {"kind": "node", "node": "g1", "check": c["id"] + "-residue"}, "attempt": row["attempt"],
        "requirement": "residue adjudicated", "type": "review", "isolation": {"kind": "fresh_subagent", "subagent": "a" + "1" * 16},
        "fails_when": c["fails_when"], "red_evidence": {"kind": "mutant", "variant_path": "r.txt", "mutation": "planted miss"},
        "verdict": "pass", "evidence": {"kind": "excerpt", "sections": [{"section": "residue", "verdict": "pass", "excerpt": "all clear"}]}})
    rec["progress"]["subagents"].append({"id": "a" + "1" * 16, "role": "reviewer", "node": "g1", "tier": "opus"})
    code, out = run(rec, tmp_path); assert code == 0, out

def test_partial_residue_verdict_must_match(tmp_path):
    rec = load(); c, row = _partial(rec)
    rec["checks"]["rows"].append({"subject": {"kind": "node", "node": "g1", "check": c["id"] + "-residue"}, "attempt": row["attempt"],
        "requirement": "residue adjudicated", "type": "review", "isolation": {"kind": "fresh_subagent", "subagent": "a" + "1" * 16},
        "fails_when": c["fails_when"], "red_evidence": {"kind": "mutant", "variant_path": "r.txt", "mutation": "planted miss"},
        "verdict": "fail", "evidence": {"kind": "excerpt", "sections": [{"section": "residue", "verdict": "fail", "excerpt": "miss at L3"}]}})
    rec["progress"]["subagents"].append({"id": "a" + "1" * 16, "role": "reviewer", "node": "g1", "tier": "opus"})
    code, out = run(rec, tmp_path); assert code == 1 and "X28" in out


# D36 follow-up: unavailable is required per check with exec_available no, not only on review-only nodes

def test_unavailable_required_when_any_check_is_no(tmp_path):
    rec = load(); n = g1(rec)
    n["checks"].append({"id": "g1-rev", "type": "review", "content": "x", "fails_when": "y", "exec_available": "no"})
    n["reviewer_tier"] = "opus"
    rec["checks"]["rows"].append({"subject": {"kind": "node", "node": "g1", "check": "g1-rev"}, "attempt": 1, "requirement": "x", "type": "review",
        "isolation": {"kind": "not_run", "reason": "not yet"}, "fails_when": "y", "red_evidence": {"kind": "not_run", "reason": "pending"},
        "verdict": "unresolved", "evidence": {"kind": "not_run", "reason": "not yet"}})
    code, out = run(rec, tmp_path); assert code == 1 and "unavailable" in out
    n["unavailable"] = {"tried": [{"what": "exec", "returned": "no oracle"}]}
    code, out = run(rec, tmp_path); assert code == 0, out


# D39 pending unknowns --------------------------------------------------------------

def _pending(rec):
    rec["framing"]["unknowns"].append({"id": "u9", "text": "open question", "changes_outcome": True, "disposition": "pending", "issue": "oi9"})
    rec["progress"]["open_issues"].append({"id": "oi9", "kind": "blocker", "text": "q", "tried": [{"what": "x", "returned": "y"}], "resolves": "answer"})

def test_pending_requires_blocked_next_action(tmp_path):
    rec = load(); _pending(rec)
    code, out = run(rec, tmp_path); assert code == 1 and "X29" in out
    rec["progress"]["next_action"] = {"kind": "blocked", "issue": "oi9"}
    code, out = run(rec, tmp_path); assert code == 0, out

def test_pending_with_answer_rejected(tmp_path):
    rec = load(); _pending(rec); rec["framing"]["unknowns"][-1]["answer"] = "x"
    rec["progress"]["next_action"] = {"kind": "blocked", "issue": "oi9"}
    assert run(rec, tmp_path)[0] == 1

def test_asked_still_requires_answer(tmp_path):
    rec = load(); rec["framing"]["unknowns"].append({"id": "u9", "text": "q", "changes_outcome": True, "disposition": "asked"})
    assert run(rec, tmp_path)[0] == 1


def test_reserve_runs_capped_at_tenth(tmp_path):
    rec = load(); rec["progress"]["usage"]["limit"] = 20; rec["progress"]["usage"]["unit"] = "node_runs"
    node = rec["checks"]["rows"][0]["subject"]["node"]; att = rec["checks"]["rows"][0]["attempt"]
    rec["progress"]["usage"]["reserve_runs"] = [{"node": node, "attempt": max(att, 2), "kind": "re_gate"}] * 3
    assert run(rec, tmp_path)[0] == 1  # 3 > ceil(20/10)


def test_reserve_run_needs_a_row(tmp_path):
    rec = load(); rec["progress"]["usage"]["limit"] = 50; rec["progress"]["usage"]["unit"] = "node_runs"
    rec["progress"]["usage"]["reserve_runs"] = [{"node": "no-such-node", "attempt": 2, "kind": "correction_return"}]
    assert run(rec, tmp_path)[0] == 1


# D54 (v3.4): integration and audit runs are reserve events of their own kind; audits alone may pass the limit
def _integ_attempts(rec):
    return {r["attempt"] for r in rec["checks"]["rows"] if r["subject"]["kind"] in ("integration", "acceptance")}

def test_reserve_audit_entries_not_counted_against_cap(tmp_path):
    rec = load(); rec["progress"]["usage"]["limit"] = 10; rec["progress"]["usage"]["unit"] = "node_runs"
    rec["progress"]["usage"]["reserve_runs"] = [{"kind": "audit", "audit": "evidence"}, {"kind": "audit", "audit": "wellformed"}]
    code, out = run(rec, tmp_path); assert code == 0, out

def test_reserve_audit_listed_twice_rejected(tmp_path):
    rec = load(); rec["progress"]["usage"]["unit"] = "node_runs"
    rec["progress"]["usage"]["reserve_runs"] = [{"kind": "audit", "audit": "evidence"}] * 2
    code, out = run(rec, tmp_path); assert code == 1 and "X30" in out

def test_consumed_may_exceed_limit_only_by_audits(tmp_path):
    rec = load(); u = rec["progress"]["usage"]; u["unit"] = "node_runs"; u["limit"] = 10; u["consumed"] = 11
    u["reserve_runs"] = []
    code, out = run(rec, tmp_path); assert code == 1 and "X30" in out
    u["reserve_runs"] = [{"kind": "audit", "audit": "evidence"}]
    code, out = run(rec, tmp_path); assert code == 0, out
    u["consumed"] = 12
    code, out = run(rec, tmp_path); assert code == 1 and "X30" in out

def test_reserve_integration_entry_needs_integration_row(tmp_path):
    rec = load(); u = rec["progress"]["usage"]; u["unit"] = "node_runs"; u["limit"] = 50
    u["reserve_runs"] = [{"kind": "integration", "attempt": 99}]
    code, out = run(rec, tmp_path); assert code == 1 and "X30" in out
    atts = _integ_attempts(rec)
    if atts:
        u["reserve_runs"] = [{"kind": "integration", "attempt": min(atts)}]
        code, out = run(rec, tmp_path); assert code == 0, out

def test_reserve_entry_shapes_enforced_by_schema(tmp_path):
    rec = load(); u = rec["progress"]["usage"]; u["unit"] = "node_runs"
    u["reserve_runs"] = [{"kind": "audit", "audit": "evidence", "attempt": 1}]   # audit with attempt
    assert run(rec, tmp_path)[0] == 1
    u["reserve_runs"] = [{"kind": "correction_return", "node": "x", "attempt": 1}]  # attempt < 2
    assert run(rec, tmp_path)[0] == 1
    u["reserve_runs"] = [{"kind": "integration", "attempt": 1, "node": "x"}]  # integration with node
    assert run(rec, tmp_path)[0] == 1


# X32 (v3.5): rule coverage — every deliverable rule is exercised or listed unchecked
def test_x32_unexercised_rule_rejected(tmp_path):
    rec = load()
    rec["rules"]["rules"].append({"id": "s-extra", "spec": "/tmp/spec.md", "rule": "x", "section": "", "quote": "x", "concerns": ["deliverable"]})
    code, out = run(rec, tmp_path); assert code == 1 and "X32" in out
    rec["progress"]["unchecked_rules"] = [{"id": "s-extra", "reason": "no check reaches it; reported at delivery"}]
    code, out = run(rec, tmp_path); assert code == 0, out

def test_x32_unchecked_must_exist_and_not_be_exercised(tmp_path):
    rec = load()
    rec["progress"]["unchecked_rules"] = [{"id": "no-such-rule", "reason": "r"}]
    code, out = run(rec, tmp_path); assert code == 1 and "X32" in out
    rec["progress"]["unchecked_rules"] = [{"id": "s-namematch", "reason": "r"}]  # exercised by c1 in the example
    code, out = run(rec, tmp_path); assert code == 1 and "both exercised" in out


# X33 (v3.5.1, D66): exec evidence commands carry absolute paths
def test_x33_relative_cd_in_exec_evidence_rejected(tmp_path):
    rec = load()
    row = next(r for r in rec["checks"]["rows"] if (r.get("evidence") or {}).get("kind") == "exec")
    row["evidence"]["command"] = "cd arm-G/graph-record && python -m pytest -q"
    code, out = run(rec, tmp_path); assert code == 1 and "X33" in out
    row["evidence"]["command"] = "cd /work/x/graph-record && python -m pytest -q"
    code, out = run(rec, tmp_path); assert code == 0, out
