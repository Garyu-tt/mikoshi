"""Capability resolution from verified live actions, not declared placeholders."""
import re


def version_key(version):
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Unsupported version constraint')
    return tuple(map(int, version.split('.')))


def owner(units, action):
    matches = []
    for unit in units.values():
        for entry in unit.get('provides', []):
            needle = entry.get('action')
            prefix = entry.get('prefix')
            if action == needle or (prefix and action.startswith(prefix)):
                matches.append((len(needle or prefix), unit['id']))
    if not matches:
        return None
    matches.sort(reverse=True)
    if len(matches)>1 and matches[0][0]==matches[1][0]:
        raise ValueError('Ambiguous capability owner: ' + action)
    return matches[0][1]


def eligible(units, toggles):
    result = {}
    def visit(key):
        if key in result:
            return result[key]
        parent = units[key].get('parent')
        value = toggles.get(key, units[key].get('enabled', True))
        result[key] = bool(value) and (parent is None or visit(parent))
        return result[key]
    for key in units:
        visit(key)
    return result


def resolve(units, toggles, live, request=None):
    if request is not None and not isinstance(request, dict):
        raise ValueError('Invalid capability request')
    active = eligible(units, toggles)
    providers = []
    for unit in units.values():
        if not active[unit['id']]:
            continue
        for item in unit.get('provides', []):
            actions = [a for a in live if a == item.get('action') or
                       item.get('prefix') and a.startswith(item['prefix'])]
            for action in actions:
                providers.append({'name':item['name'],'version':item.get('version', unit['version']),
                    'unit':unit['id'],'action':action})
    providers.sort(key=lambda x:(version_key(x['version']),x['unit'],x['action']),reverse=True)
    if request is None:
        return providers
    required = version_key(request.get('minimum','0.0.0'))
    name = request.get('name')
    if not isinstance(name, str):
        raise ValueError('Missing requested capability')
    return next((p for p in providers if p['name']==name and
                 version_key(p['version'])>=required and
                 (not request.get('unit') or p['unit']==request['unit'])), None)
