"""Exercise the stated X27 reference contract, including a repaired record."""
from test_v2_rules import load, run


def test_unknown_progress_assumption_rejects_then_restores(tmp_path):
    rec = load()
    original = rec['progress']['assumptions'][0]['id']
    rec['progress']['assumptions'][0]['id'] = 'not-in-framing'
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X27' in out, out
    rec['progress']['assumptions'][0]['id'] = original
    code, out = run(rec, tmp_path)
    assert code == 0, out


def test_risk_id_does_not_resolve_an_assumption(tmp_path):
    rec = load()
    rec['progress']['assumptions'][0]['id'] = rec['framing']['risks'][0]['id']
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X27' in out, out


def test_progress_may_reference_a_subset_of_framing_assumptions(tmp_path):
    rec = load()
    rec['progress']['assumptions'] = []
    code, out = run(rec, tmp_path)
    assert code == 0, out
