import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('release_layout', Path(__file__).parents[1] / 'scripts/test_release.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def marker(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# marker only; never executed')


def test_assembled_skill_layout(tmp_path):
    marker(tmp_path / 'skill/kit/graph-record/validate.py')
    assert m.kit_root(tmp_path / 'skill') == tmp_path / 'skill/kit'


def test_flat_v34_optional_adapter_layout(tmp_path):
    marker(tmp_path / 'release/graph-record/validate.py')
    (tmp_path / 'release/compat/codex').mkdir(parents=True)
    assert m.kit_root(tmp_path / 'release/compat/codex') == tmp_path / 'release'


def test_missing_layout_stops_before_running_commands(tmp_path):
    with pytest.raises(ValueError, match='No graph-record validator'):
        m.kit_root(tmp_path / 'missing')


def test_unrelated_ancestor_is_not_inferred_as_a_kit(tmp_path):
    marker(tmp_path / 'graph-record/validate.py')
    with pytest.raises(ValueError):
        m.kit_root(tmp_path / 'unrelated/child')


def test_raw_runner_receipt_covers_executed_core(tmp_path, monkeypatch):
    release = tmp_path / 'release'
    marker(release / 'graph-record/validate.py')
    marker(release / 'graph-record/graph-record.schema.json')
    marker(release / 'compat/codex/scripts/test_release.py')
    monkeypatch.setattr(m, '__file__', str(release / 'compat/codex/scripts/test_release.py'))
    monkeypatch.setattr(m.sys, 'argv', ['test_release.py', '--output', str(tmp_path / 'results')])
    commands = []
    def successful_command(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout='synthetic runner fixture', stderr='')
    monkeypatch.setattr(m.subprocess, 'run', successful_command)
    assert m.main() == 0
    receipt = json.loads((tmp_path / 'results/receipt.json').read_text())
    assert len(commands) == 3
    assert 'graph-record/validate.py' in receipt['files']
    assert 'graph-record/graph-record.schema.json' in receipt['files']
    assert 'compat/codex/scripts/test_release.py' in receipt['files']


def test_publishing_repository_layout(tmp_path):
    marker(tmp_path / 'repo/plugins/graph-prompt/skills/graph-record/scripts/validate.py')
    (tmp_path / 'repo/compat/codex').mkdir(parents=True)
    skills = tmp_path / 'repo/plugins/graph-prompt/skills'
    assert m.kit_root(tmp_path / 'repo/compat/codex') == skills
    assert m.record_dir(tmp_path / 'repo/compat/codex') == skills / 'graph-record/scripts'
    marker(tmp_path / 'skill/kit/graph-record/validate.py')
    assert m.record_dir(tmp_path / 'skill') == tmp_path / 'skill/kit/graph-record'


def test_this_checkout_resolves_its_own_kit():
    here = Path(__file__).resolve().parents[1]
    assert (m.record_dir(here) / 'validate.py').is_file() and (m.record_dir(here) / 'example').is_dir()


def test_repository_runner_receipt_covers_executed_core(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    marker(repo / 'plugins/graph-prompt/skills/graph-record/scripts/validate.py')
    marker(repo / 'plugins/graph-prompt/skills/graph/SKILL.md')
    marker(repo / 'compat/codex/scripts/test_release.py')
    monkeypatch.setattr(m, '__file__', str(repo / 'compat/codex/scripts/test_release.py'))
    monkeypatch.setattr(m.sys, 'argv', ['test_release.py', '--output', str(tmp_path / 'results')])
    monkeypatch.setattr(m.subprocess, 'run', lambda command, **kwargs: SimpleNamespace(returncode=0, stdout='synthetic', stderr=''))
    assert m.main() == 0
    receipt = json.loads((tmp_path / 'results/receipt.json').read_text())
    assert 'repository:graph-record/scripts/validate.py' in receipt['repository_files']
    assert 'repository:graph/SKILL.md' in receipt['repository_files']
    assert 'scripts/test_release.py' in receipt['files']
