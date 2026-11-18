"""Enforce AI prompt-size budget on editable source, not Git internals/legal text."""
from pathlib import Path

EXEMPT_DIRS = frozenset(('.git', '.venv', '__pycache__', '.pytest_cache', 'node_modules'))
EXEMPT_FILES = frozenset(('LICENSE',))
EXEMPT_SUFFIXES = frozenset(('.pyc', '.engram', '.zip'))
LIMIT = 5000


def oversized(root):
    root = Path(root)
    errors = []
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if (not path.is_file() or any(p in EXEMPT_DIRS for p in relative.parts)
                or path.name in EXEMPT_FILES or path.suffix in EXEMPT_SUFFIXES):
            continue
        size = path.stat().st_size
        if size > LIMIT:
            errors.append((relative.as_posix(), size))
    return errors


def main():
    root = Path(__file__).resolve().parent.parent
    bad = oversized(root)
    if bad:
        print('FAIL: oversized editable files', bad)
        return 1
    print('PASS: every editable source file <= 5000 bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
