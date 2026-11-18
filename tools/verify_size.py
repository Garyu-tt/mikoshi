"""Reject monolithic editable files; binary Engram containers are data, not code."""
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
bad = [(p.relative_to(root).as_posix(), p.stat().st_size)
       for p in root.rglob('*') if p.is_file()
       and p.suffix not in ('.pyc', '.engram', '.zip')
       and '__pycache__' not in p.parts and p.stat().st_size > 5000]
if bad:
    print('FAIL: oversized editable files', bad)
    raise SystemExit(1)
print('PASS: every editable file <= 5000 bytes')
