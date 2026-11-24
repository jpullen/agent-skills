"""Tests of the synthetic scenario suite itself (synth/, harness/scenarios.py). Run: python3 -m pytest -q test_synth.py"""
import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "synth"))
sys.path.insert(0, str(HERE.parents[4] / "harness"))
import catalog  # noqa: E402
import engine  # noqa: E402
import scenarios  # noqa: E402


def by_id(sid):
    return next(s for s in catalog.scenarios() if s["id"] == sid)


def run(spec, tmp):
    return json.loads(json.dumps(engine.Scenario(spec, tmp).run()))


def test_catalog_is_deterministic_and_covers_every_pair():
    a, b = catalog.scenarios(), catalog.scenarios()
    assert a == b and catalog.suite_digest(a) == catalog.suite_digest(b)
    chosen, npairs = catalog.pairwise()
    pairs = lambda c: {((i, c[i]), (j, c[j])) for i in range(len(c)) for j in range(i + 1, len(c))}
    assert len(set().union(*(pairs(c) for c in chosen))) == npairs
    assert len({s["id"] for s in a}) == len(a)
    assert all(catalog.make(*c) is not None for c in chosen)


def test_every_corruption_is_assigned():
    assigned = {c for s in catalog.scenarios() for c in s["corruptions"]}
    assert assigned == set(catalog.CORRUPTIONS)


def test_a_scenario_is_reproducible_to_the_commit(tmp_path):
    spec = by_id("named-upstream-then-late")
    one, two = run(spec, tmp_path / "1"), run(spec, tmp_path / "2")
    assert one == two and catalog.check(spec, one) == []
    assert all(len(a["commit"]) == 40 for att in one["attempts"].values() for a in att)


def test_the_oracle_fails_a_wrong_behaviour(tmp_path, monkeypatch):
    """Red evidence for the suite: a builder that does not undo its stray write must be reported, not absorbed."""
    spec = by_id("named-compound-diamond")
    real = engine.Scenario.build

    def no_undo(self, n, behavior, tree):
        return real(self, n, "good" if behavior == "undo" else behavior, tree)
    monkeypatch.setattr(engine.Scenario, "build", no_undo)
    try:
        fp = run(spec, tmp_path)
        assert catalog.check(spec, fp), "the oracle accepted a run whose retry kept an out-of-scope write"
    except RuntimeError as e:
        assert "no pass" in str(e)


def test_the_oracle_fails_a_wrong_landing():
    spec = by_id("single-none-root-none-ff")
    fp = {"outcome": "delivered", "calls": [], "attempts": {"a": [{"mode": "first", "verdict": "pass"}]}, "integration": [{"accept": {"k1": "pass", "k2": "pass"}}],
          "history": {"failed_index": []}, "landed": {"kind": "squashed"}, "probes": {}, "cleanup": {"exit": 0}, "corruptions": {},
          "audits": {"validate_audit1": 0, "validate_delivery": 0, "coverage": 0, "report": "status: complete", "verify_audit1": [0, []],
                     "verify_delivery": [0, []], "verify_after_cleanup": [0, []], "evidence": [1, 0, 0]}}
    bad = catalog.check(spec, fp)
    assert any("landed squashed" in b for b in bad) and any("history call exited 0" in b for b in bad)


def test_compare_reports_a_changed_fingerprint(capsys):
    doc = {"suite_digest": "x", "scenarios": {"s1": {"fingerprint": {"main": "a" * 40, "calls": [["land", 0]]}, "mismatches": [], "timing": 1.0}}}
    same = copy.deepcopy(doc); same["scenarios"]["s1"]["timing"] = 9.0
    assert scenarios.compare_docs(doc, same) == 0
    changed = copy.deepcopy(doc); changed["scenarios"]["s1"]["fingerprint"]["calls"] = [["land", 5]]
    assert scenarios.compare_docs(doc, changed) == 1
    assert "calls[0][1]: 0 → 5" in capsys.readouterr().out
