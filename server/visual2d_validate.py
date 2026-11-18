"""Strict 2D organ graph contract; a view never creates missing neurons."""
import math
import re

VALID_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,120}$")
ORGANS = frozenset(('brain', 'retina', 'spinal'))
LANES = frozenset(('sensory', 'interneuron', 'motor', 'other'))


def check(view):
    if not isinstance(view, dict) or view.get('schema') != 'mikoshi.visual2d.v1':
        raise ValueError('Unknown visual 2D schema')
    if view.get('organ') not in ORGANS or not VALID_ID.fullmatch(str(view.get('id', ''))):
        raise ValueError('Invalid 2D organ or identity')
    if view.get('projection') not in ('topology', 'retinotopic', 'segmental'):
        raise ValueError('Projection must be declared')
    if view.get('coordinate_kind') not in ('source', 'derived'):
        raise ValueError('Coordinate provenance required')
    if not isinstance(view.get('source'), dict) or not view['source'].get('id'):
        raise ValueError('Real source provenance required')
    points, edges = view.get('nodes'), view.get('edges')
    if not isinstance(points, list) or not isinstance(edges, list):
        raise ValueError('Missing nodes or edges')
    if len(points) > 50000 or len(edges) > 150000:
        raise ValueError('2D projection must be partitioned into smaller views')
    ids = set()
    for p in points:
        if not isinstance(p, dict) or not isinstance(p.get('id'), str):
            raise ValueError('Invalid neuron vertex')
        if not VALID_ID.fullmatch(p['id']) or p['id'] in ids:
            raise ValueError('Duplicate/invalid neuron ID')
        ids.add(p['id'])
        for key in ('x', 'y'):
            if key in p and (type(p[key]) not in (int, float)
                             or not math.isfinite(p[key]) or not 0 <= p[key] <= 1):
                raise ValueError('Nonfinite or out-of-range coordinate')
        if ('x' in p) != ('y' in p):
            raise ValueError('Incomplete 2D coordinate')
        if 'activity' in p and (type(p['activity']) not in (int, float)
                                or not math.isfinite(p['activity'])
                                or not 0 <= p['activity'] <= 1):
            raise ValueError('Invalid activity: normalized 0..1 required')
        if 'lane' in p and p['lane'] not in LANES:
            raise ValueError('Invalid spinal lane')
    for e in edges:
        if not isinstance(e, dict) or e.get('source') not in ids or e.get('target') not in ids:
            raise ValueError('Dangling neural connection')
    if view['organ'] == 'retina' and view['projection'] != 'retinotopic':
        raise ValueError('Retina must preserve real pixel coordinates')
    if view['organ'] == 'spinal' and view['projection'] != 'segmental':
        raise ValueError('Spinal view needs segmental projection')
    return view
