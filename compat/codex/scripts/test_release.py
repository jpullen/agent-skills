#!/usr/bin/env python3
"""Run reviewed release tests and mutations with durable raw outputs and receipt."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


def kit_root(skill_root):
    """Support an assembled skill, v3.4's optional compat/codex source tree, and the publishing
    repository (compat/codex beside plugins/graph-prompt/skills; see record_dir)."""
    skill_root = Path(skill_root).resolve()
    assembled = skill_root / 'kit'
    raw = skill_root.parent.parent
    if (assembled / 'graph-record/validate.py').is_file():
        return assembled
    if skill_root.name == 'codex' and skill_root.parent.name == 'compat' and (raw / 'graph-record/validate.py').is_file():
        return raw
    if repository_skills(skill_root) is not None:
        return repository_skills(skill_root)
    raise ValueError('No graph-record validator: assemble the skill, run from compat/codex in a complete v3.4 tree, '
                     'or run from compat/codex in the publishing repository')


def repository_skills(skill_root):
    skill_root = Path(skill_root).resolve()
    skills = skill_root.parent.parent / 'plugins/graph-prompt/skills'
    if skill_root.name == 'codex' and skill_root.parent.name == 'compat' and (skills / 'graph-record/scripts/validate.py').is_file():
        return skills
    return None


def record_dir(skill_root):
    """The directory holding validate.py, gen_fixtures.py and example/ for the selected layout."""
    root = kit_root(skill_root)
    return root / 'graph-record/scripts' if root == repository_skills(skill_root) else root / 'graph-record'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        selected_kit = kit_root(root)
    except ValueError as error:
        p.error(str(error))
    output = Path(a.output).resolve()
    if output == root or root in output.parents or output == selected_kit or selected_kit in output.parents:
        p.error('test output must be outside the skill directory')
    output.mkdir(parents=True, exist_ok=False)
    kit = record_dir(root)
    commands = [
        [sys.executable, '-m', 'pytest', '-q', str(kit), str(root/'tests')],
        [sys.executable, str(kit/'validate.py'), str(kit/'example'), '--models', 'haiku,sonnet,opus,fable', '--all'],
        [sys.executable, str(kit/'gen_fixtures.py'), str(kit/'example'), str(output/'mutants'), '--models', 'haiku,sonnet,opus,fable']]
    results = []
    for index, cmd in enumerate(commands):
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        logfile = output/f'{index}.log'
        logfile.write_text(r.stdout + '\nSTDERR\n' + r.stderr)
        results.append({'command': cmd, 'exit': r.returncode, 'log': logfile.name})
    receipt_root = selected_kit if selected_kit in root.parents else root
    receipt = {'python':sys.version, 'dependencies': {n:importlib.metadata.version(n) for n in ('PyYAML','jsonschema','pytest')},
               'skill_root': str(root), 'kit_root': str(selected_kit), 'receipt_root': str(receipt_root),
               'files': {f.relative_to(receipt_root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
                         for f in sorted(receipt_root.rglob('*')) if f.is_file() and not any(x in f.parts for x in ('__pycache__','.pytest_cache'))},
               'repository_files': ({'repository:' + f.relative_to(selected_kit).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
                                     for f in sorted(selected_kit.rglob('*')) if f.is_file() and not any(x in f.parts for x in ('__pycache__', '.pytest_cache'))}
                                    if selected_kit == repository_skills(root) else {}),
               'results': results, 'scope': 'supplied tests, adapter regressions, import tests, schema-derived mutants; not behavioral completion'}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(results,indent=2))
    return int(any(r['exit'] != 0 for r in results))


if __name__ == '__main__':
    sys.exit(main())
