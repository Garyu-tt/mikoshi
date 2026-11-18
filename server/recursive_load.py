"""Discover recursively nested installable units. No fixed depth or inventory."""
import json
import re
from pathlib import Path

ID = re.compile(r'^[a-z][a-z0-9_.-]{1,119}$')
KINDS = {'plugin', 'module', 'component'}


def discover(root):
    root = Path(root).resolve()
    units = {}
    for path in sorted(root.rglob('manifest.json')):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 5000:
            raise ValueError('Unsafe recursive component manifest')
        if path.parent.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Escaping component directory')
        unit = json.loads(path.read_text(encoding='utf-8'))
        if unit.get('schema') != 'adamantium.unit.v1' or unit.get('kind') not in KINDS:
            raise ValueError('Invalid unit contract: ' + str(path))
        ident = unit.get('id')
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in units:
            raise ValueError('Invalid or duplicate unit identity')
        version = unit.get('version')
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('Invalid semantic version')
        parent = unit.get('parent')
        if parent is not None and (not isinstance(parent, str) or not ID.fullmatch(parent)):
            raise ValueError('Invalid parent identifier')
        for item in unit.get('provides', []):
            if not isinstance(item, dict) or not ID.fullmatch(item.get('name', '')):
                raise ValueError('Invalid provided capability')
            if not ID.fullmatch(item.get('action', '')) and not ID.fullmatch(item.get('prefix', '')):
                raise ValueError('Capability must bind a real action or prefix')
        for item in unit.get('requires', []):
            if not isinstance(item, dict) or not ID.fullmatch(item.get('name', '')):
                raise ValueError('Invalid capability requirement')
        if unit.get('isolation', 'inprocess') != 'inprocess':
            raise ValueError('Unimplemented isolation must not be advertised')
        units[ident] = {**unit, '_path':path.parent.relative_to(root).as_posix()}
    for ident, unit in units.items():
        parent = unit.get('parent')
        if parent and (parent not in units or
                       not unit['_path'].startswith(units[parent]['_path'] + '/')):
            raise ValueError('Parent must be a containing unit directory')
    return units
