from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).parents[1]/'scripts/diff_release.py'


def test_diff_valid_missing_restored(tmp_path):
    old, new = tmp_path/'old', tmp_path/'new'
    old.mkdir(); new.mkdir()
    (old/'prompt.md').write_text('before\n')
    (new/'prompt.md').write_text('after\n')
    def run(a,b):
        return subprocess.run([sys.executable,str(SCRIPT),str(a),str(b)],capture_output=True,text=True)
    valid=run(old,new)
    assert valid.returncode == 0 and '-before' in valid.stdout and '+after' in valid.stdout
    missing=run(old,tmp_path/'absent')
    assert missing.returncode == 2 and 'must exist' in missing.stderr
    both_missing=run(tmp_path/'absent1',tmp_path/'absent2')
    assert both_missing.returncode == 2
    (new/'prompt.md').write_text('before\n')
    restored=run(old,new)
    assert restored.returncode == 0 and restored.stdout == ''
