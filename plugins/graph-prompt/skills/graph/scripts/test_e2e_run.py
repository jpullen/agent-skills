"""End-to-end scenarios: a scripted lead drives worktrees.py, the gates and the run record through whole
v3.6 runs in throwaway repositories (no model calls). Each scenario ends with both audits' programs.
Run: python3 -m pytest -q test_e2e_run.py   (needs git >= 2.31, pytest, pyyaml, jsonschema)"""
import pytest

from e2e import builders as b
from e2e.lead import Lead, sh


def audits_hold(lead):
    code, out = lead.validate()
    assert code == 0, out
    code, v = lead.verify()
    assert code == 0, v


def finish(lead, expect_landed="fast_forward", squash=False, after_integration=None):
    code, ig = lead.integrate()
    assert code == 0, ig
    if after_integration:
        after_integration(ig)
    audits_hold(lead)
    rows, miscited, unfound = lead.evidence_audit()
    assert rows == 8 and miscited == 0 and unfound == 0
    code, landed = lead.deliver(squash=squash)
    assert landed["kind"] == expect_landed, landed
    audits_hold(lead)
    cov, rep, status = lead.report()
    assert (cov, rep, status) == (0, 0, "status: complete")
    return ig, landed


def test_run13_replay_planted_scope_violation_and_killed_builder(tmp_path):
    """Run 13 as a regression: two parallel nodes, an out-of-scope write (I03), a builder stopped after writing (I12)."""
    lead = Lead(tmp_path)
    assert lead.attempt("table", b.table)[0] == "pass"
    audits_hold(lead)                                                    # the record validates mid-run, before any integration (RF-59)
    parse_tree = lead.root / "parse"
    verdict, scope = lead.attempt("parse", b.parse_out_of_scope)
    assert verdict == "fail" and scope["outside"] == ["units/table.py"]  # caught before any dependent runs
    assert (lead.root / "table" / "units" / "table.py").read_text().startswith("# section: factors")  # isolation: table's tree untouched
    assert not (parse_tree / ".graph").exists()                          # the record is in no worktree
    verdict, scope = lead.attempt("parse", b.parse_undo)                 # the undo is in scope from the scope base (RF-62)
    assert verdict == "pass" and scope["changed"] == ["units/parse.py"]
    assert lead.ws[("parse", 2)]["base"] == lead.ws[("parse", 1)]["commit"] and lead.ws[("parse", 2)]["scope_base"] == lead.base
    audits_hold(lead)
    assert lead.attempt("cli", b.killed_after_writing)[0] == "pass"      # committed as it stood, then gated (RF-65)
    cli_tree = lead.root / "cli"
    assert (cli_tree / "units" / "table.py").exists() and (cli_tree / "units" / "parse.py").exists()  # both upstreams merged (RF-64)
    ig, landed = finish(lead)
    assert ig["order"] == ["parse", "table", "cli"]
    assert "placeholder" not in (lead.repo / "units" / "table.py").read_text()   # the planted write never converged
    assert sh(lead.repo, "git", "rev-parse", "HEAD").stdout.strip() == ig["commit"]
    code, out = lead.cleanup()
    assert code == 0 and out["kept"] == [] and not lead.root.exists()
    audits_hold(lead)                                                    # branches outlive worktrees: verify still holds
    assert sh(lead.repo, "git", "branch", "--list", "graph/*").stdout.count("graph/") == 5


def test_killed_before_writing_takes_base_as_commit(tmp_path):
    """G35 / RF-65: an attempt that changed nothing is a failed row whose commit is its base; the retry stacks on it."""
    lead = Lead(tmp_path)
    assert lead.attempt("table", b.table)[0] == "pass"
    assert lead.attempt("parse", b.killed_before_writing)[0] == "fail"
    empty = lead.ws[("parse", 1)]
    assert empty["commit"] == empty["base"] == lead.base and empty["changed"] == []
    audits_hold(lead)
    assert lead.attempt("parse", b.parse)[0] == "pass"
    assert lead.ws[("parse", 2)]["base"] == lead.base
    assert lead.attempt("cli", b.cli)[0] == "pass"
    finish(lead)


def test_upstream_reopened_rebuilds_base_and_integration(tmp_path):
    """Cause (b): a defect the upstream's gate missed fails the dependent; the upstream reopens; the dependent is
    re-gated on a rebuilt base with a reset scope base; integration is rebuilt from the run base."""
    lead = Lead(tmp_path, table_gate="test_table_loose.py")
    assert lead.attempt("table", b.table_wrong_message)[0] == "pass"
    assert lead.attempt("parse", b.parse)[0] == "pass"
    assert lead.attempt("cli", b.cli)[0] == "fail"                       # stderr text comes from table
    lead.reopen("table")
    assert lead.attempt("table", b.table)[0] == "pass"
    verdict, scope = lead.attempt("cli", b.nothing, cause="upstream_field")
    assert verdict == "pass" and scope["changed"] == ["cli.py"]         # the node's own work stays visible to the scope diff (RF-67)
    a1, a2 = lead.ws[("cli", 1)], lead.ws[("cli", 2)]
    assert a2["scope_base"] != a2["base"] and a2["commit"] == a2["base"]  # nothing of cli's own changed in the re-gate
    parents = sh(lead.repo, "git", "rev-list", "--parents", "-n", "1", a2["base"]).stdout.split()
    assert parents[1:] == [a2["scope_base"], a1["commit"]]               # upstream base first, then the node's earlier commit carried in
    audits_hold(lead)
    ig, _ = finish(lead)
    assert "unknown unit: " in (lead.repo / "units" / "table.py").read_text()


def test_integration_rebuilt_after_a_late_correction(tmp_path):
    """D23/D69: a correction after integration builds the next integration attempt from the run base; the stale one fails verify."""
    lead = Lead(tmp_path)
    for node, builder in (("table", b.table), ("parse", b.parse), ("cli", b.cli)):
        assert lead.attempt(node, builder)[0] == "pass"
    code, first = lead.integrate()
    assert code == 0
    lead.reopen("parse")
    assert lead.attempt("parse", lambda tree: (tree / "units" / "parse.py").write_text(b.PARSE + "\n# reviewed\n"))[0] == "pass"
    code, v = lead.verify()
    assert code == 1 and any(f.startswith("W05 parse") for f in v["findings"])      # integration a1 no longer contains parse's newest commit
    ig, _ = finish(lead)
    assert ig["branch"].endswith("/integration/a2") and ig["base"] == lead.base and ig["commit"] != first["commit"]


def test_person_branch_moved_is_not_landed(tmp_path):
    """D70: the person committed during the run; delivery is not_landed and names the integration branch."""
    lead = Lead(tmp_path)
    for node, builder in (("table", b.table), ("parse", b.parse), ("cli", b.cli)):
        assert lead.attempt(node, builder)[0] == "pass"
    (lead.repo / "README.md").write_text("# units\n")
    sh(lead.repo, "git", "add", "README.md"); sh(lead.repo, "git", "commit", "-q", "-m", "person: readme")
    person = sh(lead.repo, "git", "rev-parse", "HEAD").stdout.strip()
    ig, landed = finish(lead, expect_landed="not_landed")
    assert "fast-forward" in landed["reason"]
    assert sh(lead.repo, "git", "rev-parse", "HEAD").stdout.strip() == person and not (lead.repo / "cli.py").exists()
    assert sh(lead.repo, "git", "rev-parse", ig["branch"]).stdout.strip() == ig["commit"]


def test_conflicting_out_of_scope_write_aborts_the_fan_in(tmp_path):
    """D69: if a scope failure were ignored, the fan-in merge conflicts, aborts, and leaves no half-merged tree."""
    lead = Lead(tmp_path)
    assert lead.attempt("table", b.table)[0] == "pass"
    assert lead.attempt("parse", b.parse_out_of_scope)[0] == "fail"
    bad = lead.ws[("parse", 1)]["commit"]
    code, r = lead.wt("node", lead.repo, "--slug", "e2e-units", "--node", "cli", "--attempt", 1, "--from", lead.base,
                      "--graph", lead.run_dir / "graph.yaml", "--upstream", f"table={lead.accepted['table']}", "--upstream", f"parse={bad}")
    assert code == 3 and r["conflicts"] == ["units/table.py"]
    assert sh(lead.root / "cli", "git", "status", "--porcelain").stdout == ""


def test_history_gate_fails_and_delivery_is_squashed(tmp_path):
    """Run 14 (RF-73): every gate read the tree; a push publishes the history. A failed attempt's commit holds the
    planted file; the history gate finds it and delivery is one squashed commit."""
    lead = Lead(tmp_path)
    assert lead.attempt("table", b.table)[0] == "pass"
    assert lead.attempt("parse", b.parse_out_of_scope)[0] == "fail"
    assert lead.attempt("parse", b.parse_undo)[0] == "pass"
    assert lead.attempt("cli", b.cli)[0] == "pass"
    def history_gate(ig):
        assert "placeholder" not in (lead.root / "integration" / "units" / "table.py").read_text()   # the tree passes
        code, h = lead.history_gate("! grep -q placeholder units/table.py 2>/dev/null #")
        assert code == 1 and h["failed"] == [lead.ws[("parse", 1)]["commit"]]                         # the history does not
    ig, landed = finish(lead, expect_landed="squashed", squash=True, after_integration=history_gate)
    published = sh(lead.repo, "git", "rev-list", f"{lead.base}..main").stdout.split()
    assert published == [landed["commit"]] and landed["commit"] != ig["commit"]
    assert sh(lead.repo, "git", "log", "--format=%an <%ae>", "-1").stdout.strip() == "e2e lead <lead@e2e.invalid>"
    assert "placeholder" not in sh(lead.repo, "git", "log", "-p", f"{lead.base}..main").stdout


def test_reset_git_identity_is_refused_then_restored(tmp_path):
    """Run 14 (RF-74) and run 15 (RF-75): a container restart reset the git identity; the commit step refuses, the lead
    restores the given author under a decision and commits again, and no commit carries the wrong author."""
    lead = Lead(tmp_path)
    sh(lead.repo, "git", "config", "user.name", "Claude")
    assert lead.attempt("table", b.table)[0] == "pass"
    assert any("commit refused: git identity was Claude" in d["reason"] for d in lead.progress["decisions"])
    assert sh(lead.repo, "git", "log", "--format=%an", "-1", lead.accepted["table"]).stdout.strip() == "e2e lead"
    audits_hold(lead)                                                    # W10 finds no wrong author
