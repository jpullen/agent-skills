"""Literal source data must not become an authored confidence assertion."""
import subprocess
import sys

import pytest
import yaml

from test_v2_rules import HERE, MODELS, load, run


@pytest.mark.parametrize('quote', [
    'Proven node acceptance needs its review gate to pass first.',
    'A source says PROVEN; attribution is not endorsement.',
    'First line.\nA proven requirement is quoted here.\nLast line.',
])
def test_literal_source_quote_can_be_preserved(tmp_path, quote):
    rec = load()
    rec['rules']['rules'][0]['quote'] = quote
    code, out = run(rec, tmp_path)
    assert code == 0, out


def raw_run(tmp_path, raw_rules):
    rec = load()
    for name, data in rec.items():
        (tmp_path / (name + '.yaml')).write_text(yaml.safe_dump(data, sort_keys=False))
    (tmp_path / 'rules.yaml').write_text(raw_rules)
    result = subprocess.run([sys.executable, str(HERE / 'validate.py'), str(tmp_path),
                             '--models', MODELS, '--all'], capture_output=True, text=True)
    return result.returncode, result.stdout


def one_rule(quote, rule='Retain the evidence for each accepted node.'):
    rec = load()['rules']
    rec['rules'][0].pop('quote', None)
    # Preserve the rest of the example's rules and their graph references.
    text = yaml.safe_dump(rec, sort_keys=False)
    first = rec['rules'][0]
    text = text.replace('rule: ' + first['rule'], 'rule: ' + rule, 1)
    # Insert the exact scalar representation under the first rule.
    lines = text.splitlines(True)
    start = next(i for i, line in enumerate(lines) if line.startswith('- id:'))
    lines.insert(start + 1, '  quote: ' + quote + '\n')
    return ''.join(lines)


def test_block_scalar_quote_is_exempt(tmp_path):
    raw = one_rule('|-\n    Proven source condition.\n    Another quoted sentence.')
    code, out = raw_run(tmp_path, raw)
    assert code == 0, out


@pytest.mark.parametrize('raw', [
    lambda: one_rule('"Proven source condition."') + '\n# PROVEN authored comment\n',
    lambda: one_rule('"Proven source condition." # proven inline comment'),
    lambda: one_rule('"Proven source condition."', 'Everything is proven.'),
    lambda: one_rule('&source "Proven source condition."', '*source'),
    lambda: one_rule('"An attributed source condition."', '"pr\\u006fven"'),
    lambda: one_rule('|- # proven header comment\n    Attributed source condition.'),
    lambda: one_rule('&proven "Attributed source condition."'),
])
def test_authored_claims_comments_and_aliases_still_reject(tmp_path, raw):
    code, out = raw_run(tmp_path, raw())
    assert code == 1 and 'X12' in out, out


def test_authored_claim_rejects_then_restored_quote_passes(tmp_path):
    rec = load()
    rec['rules']['rules'][0]['quote'] = 'Proven source condition.'
    original = rec['rules']['rules'][0]['rule']
    rec['rules']['rules'][0]['rule'] = 'The entire system is proven.'
    code, out = run(rec, tmp_path)
    assert code == 1 and 'X12' in out, out
    rec['rules']['rules'][0]['rule'] = original
    code, out = run(rec, tmp_path)
    assert code == 0, out
