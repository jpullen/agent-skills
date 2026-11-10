#!/usr/bin/env python3
"""Stage an untrusted ZIP without executing it; refuse overwrites and unsafe entries."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile


def inventory(root):
    root = Path(root)
    flat = (root / 'README.md').is_file() and (root / 'graph-record/validate.py').is_file()
    if flat and (root / 'kit').exists():
        raise ValueError('previous release has an ambiguous mixed layout')
    return {('kit/' if flat else '') + p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and (flat or p != root / 'import-manifest.json')}


def stage(archive, destination, previous=None):
    archive, destination = Path(archive), Path(destination)
    if previous is not None and not Path(previous).is_dir():
        raise ValueError('previous release directory does not exist')
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination already exists')
    with zipfile.ZipFile(archive) as z:
        entries, seen, total = [], set(), 0
        if len(z.infolist()) > 2000:
            raise ValueError('too many archive entries')
        for item in z.infolist():
            p = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (p.is_absolute() or '..' in p.parts or '\\' in item.filename or ':' in item.filename
                    or not p.parts or stat.S_ISLNK(mode)
                    or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))):
                raise ValueError('unsafe archive entry: ' + item.filename)
            key = p.as_posix().casefold()
            if key in seen:
                raise ValueError('duplicate archive path: ' + item.filename)
            seen.add(key)
            total += item.file_size
            if total > 20_000_000 or item.file_size > 5_000_000:
                raise ValueError('archive exceeds size budget')
            if not item.is_dir():
                entries.append((p, z.read(item)))
        required = {'README.md', 'graph-record/validate.py', 'graph-record/graph-record.schema.json'}
        paths = {str(p) for p, _ in entries}
        flat = required.issubset(paths)
        wrapped = {'kit/' + p for p in required}.issubset(paths)
        if flat and any(p.parts[0] == 'kit' for p, _ in entries):
            raise ValueError('ambiguous mixed archive layout')
        if not flat and not (wrapped and all(p.parts[0] == 'kit' for p, _ in entries)):
            raise ValueError('missing kit structure')
        source_paths = {str(PurePosixPath('kit') / p if flat else p): str(p) for p, _ in entries}
        entries = [(PurePosixPath('kit') / p if flat else p, data) for p, data in entries]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.graph-import-', dir=destination.parent))
    try:
        for p, data in entries:
            target = temp / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        current = inventory(temp)
        old = inventory(Path(previous)) if previous else {}
        manifest = {'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                    'archive_layout': 'flat' if flat else 'kit-prefix', 'source_paths': source_paths,
                    'files': current, 'added': sorted(current.keys() - old.keys()),
                    'removed': sorted(old.keys() - current.keys()),
                    'changed': sorted(k for k in current.keys() & old.keys() if current[k] != old[k]),
                    'status': 'staged-unreviewed; no code executed'}
        (temp / 'import-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # Exclusive destination creation prevents replacing an existing run/release.
        destination.mkdir()
        try:
            for child in temp.iterdir():
                shutil.move(str(child), destination / child.name)
        except Exception:
            shutil.rmtree(destination)
            raise
        return manifest
    finally:
        shutil.rmtree(temp)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('archive'); p.add_argument('destination'); p.add_argument('--previous')
    args = p.parse_args()
    try:
        result = stage(args.archive, args.destination, args.previous)
    except (ValueError, OSError, zipfile.BadZipFile) as e:
        p.exit(2, str(e) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
