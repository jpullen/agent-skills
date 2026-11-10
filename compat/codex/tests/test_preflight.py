"""Dispatch gate regressions. Synthetic review receipts are fixtures, not live reviews."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/preflight.py'
MODELS = 'haiku,sonnet,opus,fable'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')


def read_json(p):
    return json.loads(p.read_text())


def command(root, action, *args):
    return subprocess.run([sys.executable, str(SCRIPT), action, str(root), '--models', MODELS, *args], capture_output=True, text=True)


def ready_fixture(tmp_path):
    root = tmp_path / 'run'
    root.mkdir()
    example = ROOT / 'kit/graph-record/example'
    rec = {p.stem: yaml.safe_load(p.read_text()) for p in example.glob('*.yaml')}
    rec['progress']['graph'] = {k: (['g1', 'g3'] if k == 'not_started' else []) for k in rec['progress']['graph']}
    rec['progress']['subagents'] = []
    rec['progress']['audits']['evidence'] = {'isolation': {'kind': 'not_run', 'reason': 'not dispatched'},
        'rows': 0, 'miscited': 0, 'unfound': 0, 'verdict': 'not_run', 'notes': []}
    rec['progress']['usage']['consumed'] = 0
    source = root / 'selected-source.txt'
    source.write_text('\n'.join(r['quote'] for r in rec['rules']['rules']) + '\n')
    for rule in rec['rules']['rules']:
        rule['spec'] = 'selected'
    gate = root / 'gate.py'
    gate.write_text("assert False, 'intentional protocol fixture baseline'\n")
    actual = subprocess.run([sys.executable, str(gate)], cwd=root, capture_output=True, text=True)
    assert actual.returncode == 1 and 'AssertionError' in actual.stderr
    (root / 'baseline.log').write_text(actual.stdout + actual.stderr)
    write_json(root / 'baseline.json', {'command': [sys.executable, str(gate)], 'cwd': str(root),
        'actual_exit': actual.returncode, 'assertion_failures': 1, 'log_path': 'baseline.log',
        'inputs': [{'path': 'gate.py', 'sha256': sha(gate)}]})
    definitions = {(n['id'], c['id']): c for n in rec['graph']['nodes'] for c in n['checks']}
    rules = [r['id'] for r in rec['rules']['rules']]
    for row in rec['checks']['rows']:
        s = row['subject']
        if s['kind'] == 'node':
            c = definitions[s['node'], s['check']]
            row['requirement'], row['fails_when'] = c['content'], c['fails_when']
        if s['kind'] == 'acceptance':
            row['exercises'] = rules
        if row['type'] == 'exec':
            row['verdict'] = 'fail'
            row['evidence'] = {'kind': 'exec', 'command': sys.executable + ' gate.py',
                'expected_exit': 0, 'actual_exit': actual.returncode, 'output': actual.stderr}
        else:
            row.update(verdict='unresolved', isolation={'kind': 'not_run', 'reason': 'pre-dispatch'},
                red_evidence={'kind': 'not_run', 'reason': 'planned mutant'}, evidence={'kind': 'not_run', 'reason': 'no review yet'})
    for name, value in rec.items():
        (root / (name + '.yaml')).write_text(yaml.safe_dump(value, sort_keys=False))
    a = next(r for r in rec['checks']['rows'] if r['subject']['kind'] == 'acceptance')
    i = next(r for r in rec['checks']['rows'] if r['subject']['kind'] == 'integration')
    plan = {'version': 1, 'run_id': 'test-run', 'author': '/test/author',
        'sources': [{'id': 'selected', 'path': source.name, 'sha256': sha(source), 'role': 'normative', 'scope': 'complete synthetic two-rule source'}],
        'coverage': [{'rule_id': r, 'source_id': 'selected', 'checks': ['acceptance:c1'], 'unchecked_reason': None} for r in rules],
        'acceptance': [{**{k: a[k] for k in ('type', 'requirement', 'fails_when', 'exercises')}, 'id': 'c1', 'red_plan': 'assertion-failing baseline'}],
        'integration': {**{k: i[k] for k in ('requirement', 'fails_when')}, 'red_plan': 'same deliberate integration baseline'},
        'frozen_files': ['gate.py'],
        'baselines': [{'check': target, 'receipt': 'baseline.json'} for target in ['node:g1:g1-gate', 'acceptance:c1', 'integration']]}
    write_json(root / 'dispatch-plan.json', plan)
    return root


def review(root):
    packet = read_json(root / 'review-packet.json')
    s = packet['snapshot']
    write_json(root / 'dispatch-review.json', {'packet_sha256': sha(root / 'review-packet.json'),
        'reviewer': '/test/reviewer', 'independent_of': [s['author']], 'verdict': 'pass',
        'source_coverage': s['source_ids'], 'rule_coverage': s['rule_ids'],
        'acceptance_coverage': s['acceptance_ids'], 'residue_coverage': s.get('residue_ids', []),
        'notes': ['Synthetic fixture only, not real semantic-review evidence.']})


def prepare(root):
    p = command(root, 'prepare')
    assert p.returncode == 0, p.stdout + p.stderr
    review(root)


def test_valid_dispatch_and_mutable_progress(tmp_path):
    root = ready_fixture(tmp_path)
    prepare(root)
    p = command(root, 'seal')
    assert p.returncode == 0, p.stdout + p.stderr
    progress = yaml.safe_load((root / 'progress.yaml').read_text())
    progress['graph']['not_started'].remove('g1')
    progress['graph']['running'].append('g1')
    progress['usage']['consumed'] = 1
    (root / 'progress.yaml').write_text(yaml.safe_dump(progress))
    p = command(root, 'verify')
    assert p.returncode == 0, p.stdout + p.stderr


@pytest.mark.parametrize('change,expected', [
    ('missing_coverage', 'coverage must enumerate'),
    ('missing_acceptance', 'acceptance definitions'),
    ('unknown_check', 'unknown check'),
    ('unmapped', 'mapped checks or explicit'),
    ('bad_quote', 'quote absent'),
    ('missing_baseline', 'baseline required'),
    ('no_assertion_count', 'lacks assertion failure'),
    ('import_error_log', 'log lacks assertion failure'),
    ('changed_source', 'source drift'),
    ('escape', 'escapes run'),
    ('initial_started', 'not_started'),
])
def test_incomplete_dispatch_rejected_without_receipt(tmp_path, change, expected):
    root = ready_fixture(tmp_path)
    plan_path = root / 'dispatch-plan.json'
    plan = read_json(plan_path)
    if change == 'missing_coverage': plan['coverage'].pop()
    elif change == 'missing_acceptance': plan['acceptance'] = []
    elif change == 'unknown_check': plan['coverage'][0]['checks'] = ['node:g1:absent']
    elif change == 'unmapped': plan['coverage'][0]['checks'] = []
    elif change == 'missing_baseline': plan['baselines'].pop()
    elif change == 'escape': plan['sources'][0]['path'] = '../outside.txt'
    elif change == 'changed_source': (root / 'selected-source.txt').write_text('changed')
    elif change == 'import_error_log': (root / 'baseline.log').write_text('ModuleNotFoundError: no yaml\n')
    elif change == 'no_assertion_count':
        b = read_json(root / 'baseline.json'); b['assertion_failures'] = 0; write_json(root / 'baseline.json', b)
    elif change == 'bad_quote':
        rules = yaml.safe_load((root / 'rules.yaml').read_text()); rules['rules'][0]['quote'] = 'absent from actual source'
        (root / 'rules.yaml').write_text(yaml.safe_dump(rules))
    elif change == 'initial_started':
        progress = yaml.safe_load((root / 'progress.yaml').read_text())
        progress['graph']['not_started'].remove('g1'); progress['graph']['running'].append('g1')
        (root / 'progress.yaml').write_text(yaml.safe_dump(progress))
    write_json(plan_path, plan)
    p = command(root, 'prepare')
    assert p.returncode == 2 and expected in p.stderr, p.stdout + p.stderr
    assert not (root / 'review-packet.json').exists()


def test_explicit_unchecked_rule_is_reported(tmp_path):
    root = ready_fixture(tmp_path)
    plan = read_json(root / 'dispatch-plan.json')
    rule = plan['coverage'][0]['rule_id']
    plan['coverage'][0].update(checks=[], unchecked_reason='out of this qualification scope')
    plan['acceptance'][0]['exercises'].remove(rule)
    write_json(root / 'dispatch-plan.json', plan)
    checks = yaml.safe_load((root / 'checks.yaml').read_text())
    next(r for r in checks['rows'] if r['subject']['kind'] == 'acceptance')['exercises'].remove(rule)
    (root / 'checks.yaml').write_text(yaml.safe_dump(checks))
    prepare(root)
    assert read_json(root / 'review-packet.json')['snapshot']['unchecked_rules'] == {rule: 'out of this qualification scope'}


@pytest.mark.parametrize('field,value,expected', [
    ('packet_sha256', '0' * 64, 'different packet'),
    ('rule_coverage', [], 'incomplete semantic'),
    ('source_coverage', [], 'incomplete semantic'),
    ('acceptance_coverage', [], 'incomplete semantic'),
    ('reviewer', '/test/author', 'independent reviewer'),
    ('verdict', 'fail', 'did not pass'),
    ('notes', [], 'nonempty string list'),
])
def test_bad_or_incomplete_semantic_review_cannot_seal(tmp_path, field, value, expected):
    root = ready_fixture(tmp_path)
    prepare(root)
    data = read_json(root / 'dispatch-review.json'); data[field] = value
    write_json(root / 'dispatch-review.json', data)
    p = command(root, 'seal')
    assert p.returncode == 2 and expected in p.stderr, p.stdout + p.stderr
    assert not (root / 'dispatch-seal.json').exists()


@pytest.mark.parametrize('target', ['selected-source.txt', 'gate.py', 'dispatch-review.json', 'checks.yaml'])
def test_sealed_drift_rejected(tmp_path, target):
    root = ready_fixture(tmp_path); prepare(root)
    assert command(root, 'seal').returncode == 0
    path = root / target
    if target == 'dispatch-review.json':
        data = read_json(path); data['notes'].append('changed'); write_json(path, data)
    elif target == 'checks.yaml':
        data = yaml.safe_load(path.read_text()); data['rows'][0]['fails_when'] = 'weaker condition'; path.write_text(yaml.safe_dump(data))
    else: path.write_text(path.read_text() + '\nchanged\n')
    p = command(root, 'verify')
    assert p.returncode == 2, p.stdout + p.stderr


def test_packet_and_seal_are_exclusive(tmp_path):
    root = ready_fixture(tmp_path); prepare(root)
    packet = (root / 'review-packet.json').read_bytes()
    assert command(root, 'prepare').returncode == 2
    assert (root / 'review-packet.json').read_bytes() == packet
    assert command(root, 'seal').returncode == 0
    seal = (root / 'dispatch-seal.json').read_bytes()
    assert command(root, 'seal').returncode == 2
    assert (root / 'dispatch-seal.json').read_bytes() == seal


def test_dependency_failure_is_actionable(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('preflight_under_test', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    def absent(name):
        raise module.importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(module.importlib.metadata, 'version', absent)
    root = ready_fixture(tmp_path)
    assert module.main(['prepare', str(root), '--models', MODELS]) == 2
    assert 'selected interpreter lacks PyYAML' in capsys.readouterr().err


def test_symlink_source_escape_rejected(tmp_path):
    root = ready_fixture(tmp_path)
    outside = tmp_path / 'outside'; outside.write_text('external')
    (root / 'selected-source.txt').unlink(); (root / 'selected-source.txt').symlink_to(outside)
    p = command(root, 'prepare')
    assert p.returncode == 2 and 'escapes run' in p.stderr


def test_duplicate_json_keys_rejected(tmp_path):
    root = ready_fixture(tmp_path)
    plan = root / 'dispatch-plan.json'; body = plan.read_text()
    plan.write_text(body.replace('"version": 1', '"version": 1, "version": 1'))
    p = command(root, 'prepare')
    assert p.returncode == 2 and 'duplicate JSON key' in p.stderr


def test_runtime_instruction_drift_changes_fingerprint(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('preflight_fingerprint_test', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    package = tmp_path / 'package'; package.mkdir()
    (package / 'SKILL.md').write_text('selected instructions')
    (package / '.pytest_cache').mkdir(); (package / '.pytest_cache/runtime').write_text('cache one')
    monkeypatch.setattr(module, 'PACKAGE', package)
    before = module.toolchain_fingerprint()
    (package / '.pytest_cache/runtime').write_text('cache two')
    assert module.toolchain_fingerprint() == before
    (package / 'SKILL.md').write_text('changed instructions')
    assert module.toolchain_fingerprint() != before


@pytest.mark.parametrize('value', [[], None, 'scalar', 7])
def test_nonobject_json_root_is_not_ready(tmp_path, value):
    root = ready_fixture(tmp_path)
    write_json(root / 'dispatch-plan.json', value)
    p = command(root, 'prepare')
    assert p.returncode == 2 and 'JSON document must be an object' in p.stderr
    assert 'Traceback' not in p.stderr


def partial_fixture(tmp_path):
    root = ready_fixture(tmp_path)
    graph = yaml.safe_load((root / 'graph.yaml').read_text())
    check = graph['nodes'][0]['checks'][0]
    check.update(exec_available='partial', residue='fresh review of the flagged list')
    (root / 'graph.yaml').write_text(yaml.safe_dump(graph))
    reviewer = '/test/baseline-residue-reviewer'
    for name, body in [('flagged.txt', 'a real violation at line 3'), ('residue-mutant.txt', 'a real violation at line 3 plus a planted violation'),
                       ('residue-review.txt', 'Fail: a real violation at line 3. Synthetic test review fixture.')]:
        (root / name).write_text(body)
    write_json(root / 'residue-baseline.json', {'reviewer': reviewer, 'verdict': 'fail',
        'artifact_path': 'flagged.txt', 'artifact_sha256': sha(root / 'flagged.txt'),
        'mutant_path': 'residue-mutant.txt', 'mutant_sha256': sha(root / 'residue-mutant.txt'),
        'output_path': 'residue-review.txt', 'output_sha256': sha(root / 'residue-review.txt')})
    checks = yaml.safe_load((root / 'checks.yaml').read_text())
    checks['rows'].append({'subject': {'kind': 'node', 'node': 'g1', 'check': check['id'] + '-residue'},
        'attempt': 1, 'type': 'review', 'requirement': 'adjudicate flagged baseline', 'fails_when': check['fails_when'],
        'verdict': 'fail', 'isolation': {'kind': 'fresh_subagent', 'subagent': reviewer},
        'red_evidence': {'kind': 'mutant', 'variant_path': 'residue-mutant.txt', 'mutation': 'one extra violation'},
        'evidence': {'kind': 'excerpt', 'path': 'residue-review.txt',
            'sections': [{'section': 'residue', 'verdict': 'fail', 'excerpt': 'a real violation at line 3'}]}})
    (root / 'checks.yaml').write_text(yaml.safe_dump(checks))
    progress = yaml.safe_load((root / 'progress.yaml').read_text())
    progress['subagents'].append({'id': reviewer, 'role': 'reviewer', 'node': 'g1', 'tier': 'opus'})
    (root / 'progress.yaml').write_text(yaml.safe_dump(progress))
    plan = read_json(root / 'dispatch-plan.json')
    plan['residue_reviews'] = [{'check': 'node:g1:g1-gate', 'requirement': 'adjudicate flagged baseline',
        'fails_when': check['fails_when'], 'red_plan': 'real violation plus one planted violation', 'baseline_review': 'residue-baseline.json'}]
    write_json(root / 'dispatch-plan.json', plan)
    return root


def test_partial_residue_baseline_can_prepare_seal_verify(tmp_path):
    root = partial_fixture(tmp_path)
    prepare(root)
    assert command(root, 'seal').returncode == 0
    assert command(root, 'verify').returncode == 0


@pytest.mark.parametrize('change', ['missing_definition', 'missing_review_coverage', 'drift', 'degraded', 'wrong_mutant_path'])
def test_partial_residue_requires_defined_reviewed_immutable_baseline(tmp_path, change):
    root = partial_fixture(tmp_path)
    if change == 'missing_definition':
        plan = read_json(root / 'dispatch-plan.json'); del plan['residue_reviews']; write_json(root / 'dispatch-plan.json', plan)
    elif change == 'degraded':
        checks = yaml.safe_load((root / 'checks.yaml').read_text())
        for row in checks['rows']:
            if row['subject'].get('node') == 'g1': row['verdict'] = 'unresolved'
        row = checks['rows'][-1]
        row.update(isolation={'kind': 'not_run', 'reason': 'no reviewer available'}, red_evidence={'kind': 'not_run', 'reason': 'not run'},
                   evidence={'kind': 'not_run', 'reason': 'not reviewed'})
        (root / 'checks.yaml').write_text(yaml.safe_dump(checks))
    elif change == 'wrong_mutant_path':
        checks = yaml.safe_load((root / 'checks.yaml').read_text()); checks['rows'][-1]['red_evidence']['variant_path'] = 'different.txt'
        (root / 'checks.yaml').write_text(yaml.safe_dump(checks))
    if change in ('missing_definition', 'degraded', 'wrong_mutant_path'):
        assert command(root, 'prepare').returncode == 2
        return
    prepare(root)
    if change == 'missing_review_coverage':
        data = read_json(root / 'dispatch-review.json'); data['residue_coverage'] = []; write_json(root / 'dispatch-review.json', data)
        assert command(root, 'seal').returncode == 2
    else:
        assert command(root, 'seal').returncode == 0
        (root / 'flagged.txt').write_text('changed flags')
        assert command(root, 'verify').returncode == 2


@pytest.mark.parametrize('internal', [False, True])
def test_package_directory_symlinks_rejected(tmp_path, monkeypatch, internal):
    spec = importlib.util.spec_from_file_location('preflight_links_test', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    package = tmp_path / 'package'; package.mkdir()
    target = package / 'internal' if internal else tmp_path / 'external'
    target.mkdir(); (target / 'prompt.md').write_text('runtime contract')
    (package / 'kit').symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(module, 'PACKAGE', package)
    with pytest.raises(module.NotReady, match='directory/dangling/external'):
        module.toolchain_fingerprint()


@pytest.mark.parametrize('nested', [False, True])
def test_run_inside_package_rejected_before_packet(tmp_path, monkeypatch, capsys, nested):
    spec = importlib.util.spec_from_file_location('preflight_nested_test', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    package = tmp_path / 'package'; package.mkdir()
    root = package / 'run' if nested else package
    if nested: root.mkdir()
    monkeypatch.setattr(module, 'PACKAGE', package)
    assert module.main(['prepare', str(root), '--models', MODELS]) == 2
    assert 'outside the selected package' in capsys.readouterr().err
    assert not (root / 'review-packet.json').exists()
