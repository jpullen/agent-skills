import importlib.util
from pathlib import Path
import zipfile
import pytest

spec = importlib.util.spec_from_file_location('import_release', Path(__file__).parents[1] / 'scripts/import_release.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def archive(tmp, extra=None):
    p = tmp / 'input.zip'
    with zipfile.ZipFile(p, 'w') as z:
        for n in ('README.md','graph-record/validate.py','graph-record/graph-record.schema.json'):
            z.writestr('kit/' + n, '{}')
        if extra:
            z.writestr(*extra)
    return p


def test_import_preserves_bytes_and_reports_changes(tmp_path):
    a = archive(tmp_path)
    r = m.stage(a, tmp_path/'v1')
    assert (tmp_path/'v1/kit/README.md').read_bytes() == b'{}'
    assert len(r['files']) == 3
    r2 = m.stage(a, tmp_path/'v2', tmp_path/'v1')
    assert not r2['added'] and not r2['changed'] and not r2['removed']
    (tmp_path/'v1/kit/README.md').write_text('changed')
    r3 = m.stage(a, tmp_path/'v3', tmp_path/'v1')
    assert r3['changed'] == ['kit/README.md']


def test_existing_destination_survives(tmp_path):
    a = archive(tmp_path)
    d = tmp_path/'old'; d.mkdir(); (d/'keep').write_text('keep')
    with pytest.raises(ValueError): m.stage(a, d)
    assert (d/'keep').read_text() == 'keep'


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'kit/../../escape', 'kit\\evil', 'kit/C:drive', 'kit/readme.md'])
def test_unsafe_path_rejected_atomically(tmp_path, name):
    a = archive(tmp_path, (name, 'bad'))
    with pytest.raises(ValueError): m.stage(a, tmp_path/'new')
    assert not (tmp_path/'new').exists()


def test_symlink_rejected(tmp_path):
    info = zipfile.ZipInfo('kit/link'); info.create_system = 3; info.external_attr = 0o120777 << 16
    a = archive(tmp_path, (info, '/outside'))
    with pytest.raises(ValueError): m.stage(a, tmp_path/'new')


def test_payload_is_not_executed(tmp_path):
    a = archive(tmp_path, ('kit/evil.py', 'raise RuntimeError("must never run")'))
    assert m.stage(a, tmp_path/'new')['status'].startswith('staged-unreviewed')


def test_missing_structure_rejected(tmp_path):
    p=tmp_path/'empty.zip'
    with zipfile.ZipFile(p,'w'): pass
    with pytest.raises(ValueError): m.stage(p,tmp_path/'new')


def test_missing_previous_is_not_silent_new_baseline(tmp_path):
    with pytest.raises(ValueError):
        m.stage(archive(tmp_path),tmp_path/'new',tmp_path/'missing')
    assert not (tmp_path/'new').exists()


def test_nested_manifest_is_hashed_and_compared(tmp_path):
    a=archive(tmp_path,('kit/import-manifest.json','original'))
    first=m.stage(a,tmp_path/'v1')
    assert 'kit/import-manifest.json' in first['files']
    a=archive(tmp_path,('kit/import-manifest.json','changed'))
    second=m.stage(a,tmp_path/'v2',tmp_path/'v1')
    assert second['changed'] == ['kit/import-manifest.json']
