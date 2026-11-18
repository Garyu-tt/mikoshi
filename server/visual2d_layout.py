"""Deterministic 2D fallback for real topology and spinal segment ordering."""
import math

GOLDEN = 2.399963229728653
LANE_X = {'sensory': .15, 'interneuron': .50, 'motor': .85, 'other': .50}


def project(view):
    points = [dict(n) for n in view['nodes']]
    if view['projection'] == 'retinotopic':
        if any('x' not in p for p in points):
            raise ValueError('Photoreceptor positions cannot be invented')
    elif view['projection'] == 'segmental':
        segments = sorted({str(n.get('segment', '')) for n in points})
        if not segments or '' in segments:
            raise ValueError('Spinal nodes require segment provenance')
        ordinal = {s: i for i, s in enumerate(segments)}
        group_counts = {}
        for n in sorted(points, key=lambda p: p['id']):
            if 'x' in n:
                continue
            segment = str(n['segment']); lane = n.get('lane', 'other')
            key = (segment, lane); index = group_counts.get(key, 0)
            group_counts[key] = index + 1
            n['x'] = min(.98, LANE_X[lane] + .01 * (index % 7 - 3))
            n['y'] = (ordinal[segment] + .5 + .006*(index//7)) / len(segments)
            n['y'] = min(1.0, n['y'])
    else:
        for i, n in enumerate(sorted(points, key=lambda p: p['id'])):
            if 'x' in n:
                continue
            radius = .47 * math.sqrt((i + .5) / max(1, len(points)))
            n['x'] = .5 + radius * math.cos(i * GOLDEN)
            n['y'] = .5 + radius * math.sin(i * GOLDEN)
    return {**view, 'nodes': points, 'layout_notice': (
        'derived_2d_not_anatomical_position' if view['coordinate_kind'] == 'derived'
        else 'source_supplied_2d_coordinates')}
