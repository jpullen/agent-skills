#!/usr/bin/env python3
import argparse
import difflib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('upstream'); p.add_argument('adapted')
a = p.parse_args()
u, v = Path(a.upstream), Path(a.adapted)
if not u.is_dir() or not v.is_dir():
    p.error('both release directories must exist')
paths = {x.relative_to(root) for root in (u, v) for x in root.rglob('*') if x.is_file() and '__pycache__' not in x.parts and '.pytest_cache' not in x.parts}
for path in sorted(paths):
    old = (u/path).read_text().splitlines(True) if (u/path).exists() else []
    new = (v/path).read_text().splitlines(True) if (v/path).exists() else []
    print(''.join(difflib.unified_diff(old, new, fromfile='upstream/'+str(path), tofile='adapted/'+str(path))), end='')
