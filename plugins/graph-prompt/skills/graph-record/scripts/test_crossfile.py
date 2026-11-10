"""Unit-level cross-file rule counterexamples, separate from CLI/schema coverage."""
import copy

import pytest

from test_v2_rules import load, MODELS
from validate import crossfile_findings


@pytest.mark.parametrize('rule', [f'X{i:02}' for i in range(1, 31) if i not in (6, 19, 27, 28, 29, 30)])
def test_crossfile_rule_detects_counterexample(rule, tmp_path):
    r = load(); nodes = r['graph']['nodes']; rows = r['checks']['rows']; p = r['progress']
    if rule == 'X01': rows.pop(0)
    elif rule == 'X02': nodes[1]['reads']['upstream'][0]['sections'] = ['missing']
    elif rule == 'X03': nodes[0]['split_reason']['risk'] = 'missing'
    elif rule == 'X04': r['framing']['risks'][0]['guarded_by']['check'] = 'missing'
    elif rule == 'X05': rows[1]['isolation']['subagent'] = 'unknown'
    elif rule == 'X07': nodes[1]['reviewer_tier'] = 'haiku'
    elif rule == 'X08': nodes[0]['model']['tier'] = 'opus'
    elif rule == 'X09': rows[2]['exercises'] = ['missing']
    elif rule == 'X10': p['graph']['accepted'].pop()
    elif rule == 'X11': rows[2]['evidence'] = {'kind': 'carried', 'from_node': 'g1', 'sha256': '0'*64}
    elif rule == 'X12': (tmp_path/'graph.yaml').write_text('note: PROVEN\n')
    elif rule == 'X13': rows[0]['attempt'] = 2
    elif rule == 'X14': nodes[1]['writes'] = nodes[0]['writes'][:]
    elif rule == 'X15': nodes[0]['reads']['upstream'] = [{'node':'g3','sections':['usage']}]
    elif rule == 'X16': rows[1]['verdict'] = 'dissent'
    elif rule == 'X17': p['audits']['evidence']['miscited'] = 1
    elif rule == 'X18': p['subagents'] = [s for s in p['subagents'] if s['role'] != 'reviewer']
    elif rule == 'X20': nodes[0]['code'] = {'gate':'missing'}
    elif rule == 'X21': rows[0]['evidence']['actual_exit'] = 1
    elif rule == 'X22': nodes.append(copy.deepcopy(nodes[0]))
    elif rule == 'X23': rows[0]['subject']['check'] = 'missing'
    elif rule == 'X24': nodes[0]['does'][0]['produces'] = 'missing'
    elif rule == 'X25': nodes[0]['model']['tier_rule'] = ['review_only_check']
    elif rule == 'X26': p['audits']['evidence'].update(rows=0, verdict='fail')
    else: raise AssertionError(rule)
    findings, _ = crossfile_findings(r, MODELS.split(','), {}, str(tmp_path))
    assert rule in {f[0] for f in findings}, findings


def test_x19_prose_is_explicitly_manual(tmp_path):
    findings, manual = crossfile_findings(load(), MODELS.split(','), {}, str(tmp_path))
    assert findings == [] and manual == 1


def test_x27_unknown_assumption_reference_is_rejected(tmp_path):
    r = load(); r['progress']['assumptions'][0]['id'] = 'unknown'
    findings, _ = crossfile_findings(r, MODELS.split(','), {}, str(tmp_path))
    assert 'X27' in {finding[0] for finding in findings}
