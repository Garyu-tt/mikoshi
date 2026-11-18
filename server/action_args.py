"""Typed API arguments; preserve 64-bit timestamps sent from JS as strings."""
import re
import math

_INT = re.compile(r'^(0|[1-9][0-9]{0,18})$')


def normalize(capabilities, action, args):
    if not isinstance(args, dict):
        raise ValueError('Action arguments must be object')
    item = next((c for c in capabilities if c['id'] == action), None)
    if item is None:
        raise ValueError('Unknown capability')
    result = dict(args)
    for field in item.get('fields', []):
        name = field['name']
        if name not in result or result[name] is None:
            continue
        value = result[name]
        if field['type'] == 'number':
            if isinstance(value, str) and _INT.fullmatch(value):
                value = int(value)
            if type(value) is not int or not 0 <= value < 2**63:
                raise ValueError('Invalid integer field: ' + name)
            result[name] = value
        elif field['type'] == 'fraction':
            if isinstance(value, str) and re.fullmatch(r'(0|1)(\.0+)?|0\.[0-9]+', value):
                value = float(value)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Invalid normalized coordinate: '+name)
            result[name] = value
        elif field['type'] == 'text' and not isinstance(value, str):
            raise ValueError('Invalid text field: ' + name)
        elif field['type'] == 'json' and not isinstance(value, (dict, list)):
            raise ValueError('Invalid structured field: ' + name)
    return result
