"""v3.4 ships a flat archive; normalize paths while preserving every source byte."""
import importlib.util
from pathlib import Path
import zipfile

import pytest

spec = importlib.util.spec_from_file_location('v34_import', Path(__file__).parents[1] / 'scripts/import_release.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def flat_archive(tmp_path, extra=None):
    path = tmp_path / 'flat.zip'
    with zipfile.ZipFile(path, 'w') as z:
        for name in ['README.md', 'graph-record/validate.py', 'graph-record/graph-record.schema.json']:
            z.writestr(name, b'original bytes\n')
        z.writestr('compat/codex/scripts/import_release.py', b'raise RuntimeError("do not run")\n')
        if extra:
            z.writestr(*extra)
    return path


def test_flat_release_normalizes_without_execution(tmp_path):
    path = flat_archive(tmp_path)
    receipt = m.stage(path, tmp_path / 'staged')
    assert receipt['archive_layout'] == 'flat'
    assert receipt['source_paths']['kit/README.md'] == 'README.md'
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            assert (tmp_path / 'staged/kit' / name).read_bytes() == z.read(name)


def test_flat_and_prefixed_archives_compare_as_same_release(tmp_path):
    flat = flat_archive(tmp_path)
    m.stage(flat, tmp_path / 'one')
    wrapped = tmp_path / 'wrapped.zip'
    with zipfile.ZipFile(flat) as source, zipfile.ZipFile(wrapped, 'w') as target:
        for name in source.namelist():
            target.writestr('kit/' + name, source.read(name))
    receipt = m.stage(wrapped, tmp_path / 'two', tmp_path / 'one')
    assert receipt['archive_layout'] == 'kit-prefix'
    assert not any(receipt[k] for k in ['added', 'removed', 'changed'])


def test_flat_previous_tree_compares_with_normalized_stage(tmp_path):
    path = flat_archive(tmp_path)
    previous = tmp_path / 'previous'
    previous.mkdir()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            p = previous / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(name))
    receipt = m.stage(path, tmp_path / 'new', previous)
    assert not any(receipt[k] for k in ['added', 'removed', 'changed'])


def test_raw_flat_manifest_is_source_not_staging_metadata(tmp_path):
    path = flat_archive(tmp_path, ('import-manifest.json', b'payload'))
    previous = tmp_path / 'previous'
    previous.mkdir()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            p = previous / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(name))
    (previous / 'import-manifest.json').write_bytes(b'older payload')
    receipt = m.stage(path, tmp_path / 'new', previous)
    assert receipt['changed'] == ['kit/import-manifest.json']


@pytest.mark.parametrize('name', ['kit/README.md', '../escape', '/absolute', 'README.MD', 'graph-record/../../escape'])
def test_flat_layout_rejects_ambiguity_and_unsafe_paths(tmp_path, name):
    with pytest.raises(ValueError):
        m.stage(flat_archive(tmp_path, (name, b'bad')), tmp_path / 'new')
    assert not (tmp_path / 'new').exists()
