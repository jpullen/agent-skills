"""Regression for carrying an explicitly selected gate from a multi-check node."""
import copy
import subprocess
import sys

import pytest

from test_v2_rules import HERE, MODELS, load, run


def carried_record(*, multiple=True, explicit=True):
    rec = load()
    source = rec['graph']['nodes'][1]
    if multiple:
        check = copy.deepcopy(source['checks'][0])
        check['id'] = 'g3-other'
        source['checks'].append(check)
        row = copy.deepcopy(rec['checks']['rows'][1])
        row['subject']['check'] = 'g3-other'
        rec['checks']['rows'].append(row)
    carried = copy.deepcopy(rec['checks']['rows'][1])
    carried['subject'] = {'kind': 'acceptance', 'item': 'c2'}
    carried['exercises'] = []
    carried['evidence'] = {'kind': 'carried', 'from_node': 'g3', 'sha256': '0' * 64}
    if explicit:
        carried['evidence']['from_check'] = 'g3-review'
    rec['checks']['rows'].append(carried)
    return rec, carried


def validate(rec, tmp_path, artifact='0' * 64):
    run(rec, tmp_path)  # Serialize using the existing suite's fixture helper.
    args = [sys.executable, str(HERE / 'validate.py'), str(tmp_path / 'rec'),
            '--models', MODELS, '--all']
    if artifact is not None:
        args += ['--artifacts', 'g3=' + artifact]
    result = subprocess.run(args, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def test_multicheck_explicit_carry_passes(tmp_path):
    rec, _ = carried_record()
    code, out = validate(rec, tmp_path)
    assert code == 0, out


def test_single_check_implicit_carry_still_passes(tmp_path):
    rec, _ = carried_record(multiple=False, explicit=False)
    code, out = validate(rec, tmp_path)
    assert code == 0, out


def test_multicheck_implicit_carry_stays_ambiguous(tmp_path):
    rec, _ = carried_record(explicit=False)
    code, out = validate(rec, tmp_path)
    assert code == 1 and 'X11' in out, out


def test_unknown_explicit_check_rejected(tmp_path):
    rec, carried = carried_record()
    carried['evidence']['from_check'] = 'not-on-g3'
    code, out = validate(rec, tmp_path)
    assert code == 1 and 'X11' in out, out


def test_explicit_carry_rejects_obsolete_pass(tmp_path):
    rec, _ = carried_record()
    newer = copy.deepcopy(rec['checks']['rows'][1])
    newer.update(attempt=2, verdict='fail')
    rec['checks']['rows'].append(newer)
    rec['progress']['graph']['accepted'].remove('g3')
    rec['progress']['graph']['failed'].append('g3')
    rec['progress']['hypotheses'].append({'node': 'g3', 'before_attempt': 2,
        'cause': 'builder_error', 'disconfirmation': 'rerun the cited review'})
    code, out = validate(rec, tmp_path)
    assert code == 1 and 'X11' in out, out


@pytest.mark.parametrize('artifact', [None, '1' * 64])
def test_explicit_carry_still_requires_matching_artifact(tmp_path, artifact):
    rec, _ = carried_record()
    code, out = validate(rec, tmp_path, artifact)
    assert code == 1 and 'X11' in out, out


def test_empty_explicit_check_rejected_by_schema(tmp_path):
    rec, carried = carried_record()
    carried['evidence']['from_check'] = ''
    code, out = validate(rec, tmp_path)
    assert code == 1 and 'SCHEMA' in out, out
