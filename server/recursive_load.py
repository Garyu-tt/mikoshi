"""Discover recursively nested installable units. No fixed depth or inventory."""
import json
from pathlib import Path

from server.recursive_manifest import validate


def discover(root):
    root = Path(root).resolve()
    units = {}
    for path in sorted(root.rglob('manifest.json')):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 5000:
            raise ValueError('Unsafe recursive component manifest')
        if path.parent.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Escaping component directory')
        unit = validate(json.loads(path.read_text(encoding='utf-8')))
        ident = unit['id']
        if ident in units:
            raise ValueError('Duplicate recursive unit identity')
        units[ident] = {**unit, '_path':path.parent.relative_to(root).as_posix()}
    for ident, unit in units.items():
        parent = unit.get('parent')
        if parent and (parent not in units or
                       not unit['_path'].startswith(units[parent]['_path'] + '/')):
            raise ValueError('Parent must be a containing unit directory')
    return units
