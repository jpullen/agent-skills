"""Observed portability and evidence regressions; no live services needed."""
import copy
import json
import subprocess
import sys

import pytest
import yaml

from test_v2_rules import HERE, MODELS, load, run, _partial


@pytest.mark.parametrize('agent_id', ['019abcd0-1234-7890-abcd-0123456789ab', '/root/reviewer', 'agent_42'])
def test_opaque_runtime_agent_ids(agent_id, tmp_path):
    rec = load()
    old = rec['progress']['subagents'][2]['id']
    rec['progress']['subagents'][2]['id'] = agent_id
    for row in rec['checks']['rows']:
        if row['isolation'].get('subagent') == old:
            row['isolation']['subagent'] = agent_id
    code, out = run(rec, tmp_path)
    assert code == 0, out


def test_same_agent_cannot_build_and_review(tmp_path):
    rec = load()
    builder = next(x for x in rec['progress']['subagents'] if x.get('node') == 'g3' and x['role'] == 'builder')
    reviewer = next(x for x in rec['progress']['subagents'] if x.get('node') == 'g3' and x['role'] == 'reviewer')
    old = reviewer['id']
    reviewer['id'] = builder['id']
    for row in rec['checks']['rows']:
        if row['isolation'].get('subagent') == old:
            row['isolation']['subagent'] = builder['id']
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X06' in out, out


@pytest.mark.parametrize('args', [
    ['--artifacts', 'g1'], ['--artifacts', 'g1=bad'],
    ['--artifacts', 'g1=' + '0'*64 + ',g1=' + '1'*64],
    ['--models', 'opus,opus'], ['--models', 'opus,,sonnet']])
def test_invalid_cli_arguments_are_usage_errors(args):
    p = subprocess.run([sys.executable, str(HERE/'validate.py'), str(HERE/'example'), *args], capture_output=True, text=True)
    assert p.returncode == 2 and 'Traceback' not in p.stderr, p.stdout + p.stderr


def test_yaml_duplicate_keys_rejected(tmp_path):
    rec = load()
    run(rec, tmp_path)
    p = tmp_path/'rec'/'progress.yaml'
    p.write_text(p.read_text() + '\nnext_action: {kind: delivery}\n')
    result = subprocess.run([sys.executable, str(HERE/'validate.py'), str(p.parent), '--models', MODELS], capture_output=True, text=True)
    assert result.returncode == 2 and 'duplicate' in result.stderr.lower()


def test_duplicate_subject_attempt_is_ambiguous(tmp_path):
    rec = load()
    rec['checks']['rows'].append(copy.deepcopy(rec['checks']['rows'][0]))
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X22' in out


def test_residue_requires_fresh_review(tmp_path):
    rec = load()
    check, row = _partial(rec)
    residue = {'subject': {'kind': 'node', 'node': 'g1', 'check': check['id']+'-residue'},
               'attempt': 1, 'requirement': 'residue reviewed', 'type': 'inspect',
               'isolation': {'kind': 'na_inspect'}, 'fails_when': 'violation remains',
               'red_evidence': {'kind': 'minimal_inspect'},
               'verdict': 'pass', 'evidence': {'kind': 'location', 'path': 'output.txt', 'location': 'L1'}}
    rec['checks']['rows'].append(residue)
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X28' in out, out


def test_integration_retry_hypothesis_is_valid(tmp_path):
    rec = load()
    row = copy.deepcopy(rec['checks']['rows'][-1]); row['attempt'] = 2
    rec['checks']['rows'].append(row)
    rec['progress']['hypotheses'].append({'node': 'integration', 'before_attempt': 2, 'cause': 'builder_error', 'disconfirmation': 'rerun integration'})
    code, out = run(rec, tmp_path)
    assert code == 0, out


def test_audit_cannot_pass_when_not_run(tmp_path):
    rec = load()
    rec['progress']['audits']['evidence']['isolation'] = {'kind': 'not_run'}
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X17' in out


def test_audit_counts_cannot_exceed_rows(tmp_path):
    rec = load(); e = rec['progress']['audits']['evidence']
    e.update(rows=1, miscited=2, unfound=0, verdict='fail')
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X17' in out


def test_accepted_node_requires_passing_latest_checks(tmp_path):
    rec = load(); rec['checks']['rows'][0]['verdict'] = 'fail'
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X31' in out


def test_fixture_generator_preserves_existing_output(tmp_path):
    out = tmp_path/'existing'; out.mkdir(); (out/'keep').write_text('keep')
    p = subprocess.run([sys.executable, str(HERE/'gen_fixtures.py'), str(HERE/'example'), str(out), '--models', MODELS], capture_output=True, text=True)
    assert p.returncode == 2 and (out/'keep').read_text() == 'keep'


def test_carried_evidence_cannot_use_obsolete_pass(tmp_path):
    rec = load()
    newer = copy.deepcopy(rec['checks']['rows'][0]); newer.update(attempt=2, verdict='fail')
    rec['checks']['rows'].append(newer)
    rec['progress']['graph']['accepted'].remove('g1'); rec['progress']['graph']['failed'].append('g1')
    rec['progress']['hypotheses'].append({'node':'g1','before_attempt':2,'cause':'builder_error','disconfirmation':'rerun'})
    rec['checks']['rows'][2]['evidence'] = {'kind':'carried','from_node':'g1','sha256':'0'*64}
    run(rec, tmp_path)
    p = subprocess.run([sys.executable, str(HERE/'validate.py'), str(tmp_path/'rec'), '--models', MODELS, '--artifacts', 'g1='+'0'*64, '--all'], capture_output=True, text=True)
    assert p.returncode == 1 and 'X11' in p.stdout, p.stdout


@pytest.mark.parametrize('validator_exit', [0, 2])
def test_fixture_harness_fails_on_surviving_mutant_or_crash(tmp_path, monkeypatch, validator_exit):
    import gen_fixtures
    from types import SimpleNamespace
    monkeypatch.setattr(sys, 'argv', ['gen_fixtures.py', str(HERE/'example'), str(tmp_path/'out'), '--models', MODELS])
    calls = []
    def fake_run(*args, **kwargs):
        code = 0 if not calls else validator_exit
        calls.append(code)
        return SimpleNamespace(returncode=code, stdout='', stderr='')
    monkeypatch.setattr(gen_fixtures.subprocess, 'run', fake_run)
    assert gen_fixtures.main() == 1


def test_fixture_harness_rejects_invalid_baseline(tmp_path):
    p = subprocess.run([sys.executable, str(HERE/'gen_fixtures.py'), str(tmp_path/'missing'), str(tmp_path/'out')], capture_output=True, text=True)
    assert p.returncode == 2 and not (tmp_path/'out').exists()
