"""Fail-closed manifest contract, independent of the physical module depth."""
import re

ID = re.compile(r'^[a-z][a-z0-9_.-]{1,119}$')
VERSION = re.compile(r'^\d+\.\d+\.\d+$')
KINDS = {'plugin', 'module', 'component'}


def ident(value):
    return isinstance(value, str) and bool(ID.fullmatch(value))


def version(value):
    return isinstance(value, str) and bool(VERSION.fullmatch(value))


def _entries(items, purpose):
    if not isinstance(items, list):
        raise ValueError(purpose + ' must be a list')
    for item in items:
        if not isinstance(item, dict) or not ident(item.get('name')):
            raise ValueError('Invalid capability ' + purpose)
        if purpose == 'provides':
            exact, prefix = item.get('action'), item.get('prefix')
            if (ident(exact) and prefix is None) == (ident(prefix) and exact is None):
                raise ValueError('Provide exactly one action or prefix')
            if 'version' in item and not version(item['version']):
                raise ValueError('Invalid provided capability version')
        else:
            if 'minimum' in item and not version(item['minimum']):
                raise ValueError('Invalid requirement version')
            if 'optional' in item and type(item['optional']) is not bool:
                raise ValueError('Invalid optional requirement flag')
            if 'unit' in item and not ident(item['unit']):
                raise ValueError('Invalid requested provider identity')


def validate(unit):
    if not isinstance(unit, dict) or unit.get('schema') != 'adamantium.unit.v1':
        raise ValueError('Unsupported recursive manifest schema')
    if unit.get('kind') not in KINDS or not ident(unit.get('id')):
        raise ValueError('Invalid recursive unit identity or kind')
    if not version(unit.get('version')):
        raise ValueError('Invalid semantic version')
    parent = unit.get('parent')
    if parent is not None and not ident(parent):
        raise ValueError('Invalid parent identity')
    if unit.get('kind') == 'plugin' and parent is not None:
        raise ValueError('Installable plugin must be a root')
    if unit.get('kind') != 'plugin' and parent is None:
        raise ValueError('Module or component needs a parent')
    if unit.get('isolation', 'inprocess') != 'inprocess':
        raise ValueError('Unimplemented isolation is prohibited')
    for key in ('enabled', 'protected'):
        if key in unit and type(unit[key]) is not bool:
            raise ValueError('Invalid ' + key + ' flag')
    if unit.get('protected') and unit.get('enabled') is False:
        raise ValueError('Protected unit cannot default to disabled')
    for key in ('provides', 'requires'):
        _entries(unit.get(key, []), key)
    return unit
