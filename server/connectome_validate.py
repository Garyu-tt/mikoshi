"""A runnable connectome requires genuine explicit topology, never fabricated links."""
import math
import re
from server.visual2d_validate import VALID_ID, LANES

ID = re.compile(r"^[A-Za-z0-9_-]{1,72}$")
MAX_NEURONS = 2500
MAX_SYNAPSES = 20000


def finite(v, lo, hi):
    return type(v) in (int, float) and math.isfinite(v) and lo <= v <= hi


def check(data):
    if not isinstance(data, dict) or data.get('schema') != 'mikoshi.connectome.v1':
        raise ValueError('Unknown connectome format')
    ident, organ = data.get('id'), data.get('organ')
    if not isinstance(ident, str) or not ID.fullmatch(ident):
        raise ValueError('Connectome id must be stable and safe')
    if organ not in ('brain', 'spinal'):
        raise ValueError('Executable connectome currently supports brain/spinal only')
    if data.get('coordinate_kind') not in ('source', 'derived'):
        raise ValueError('Explicit coordinate provenance required')
    src = data.get('source')
    if not isinstance(src, dict) or not isinstance(src.get('id'), str) or not src['id']:
        raise ValueError('Missing topology provenance')
    nodes, edges = data.get('neurons'), data.get('synapses')
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NEURONS:
        raise ValueError('Neuron population exceeds safe CPU bounds')
    if not isinstance(edges, list) or len(edges) > MAX_SYNAPSES:
        raise ValueError('Synapse count exceeds safe CPU bounds')
    if not finite(data.get('dt_ms'), .1, 100):
        raise ValueError('dt_ms must be 0.1..100')
    ids = set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get('id'), str) or not VALID_ID.fullmatch(n['id']) or n['id'] in ids:
            raise ValueError('Invalid or duplicate neuron')
        ids.add(n['id'])
        if not all(finite(n.get(k), 0, 1) for k in ('x', 'y')):
            raise ValueError('Neuron requires explicit 2D coordinates')
        if not finite(n.get('tau_ms'), .5, 10000):
            raise ValueError('Invalid membrane time constant')
        if not finite(n.get('threshold'), .01, 100):
            raise ValueError('Invalid neuron threshold')
        if not finite(n.get('refractory_ms',0), 0, 10000):
            raise ValueError('Invalid refractory duration')
        if organ == 'spinal':
            if not isinstance(n.get('segment'), str) or not n['segment'].strip():
                raise ValueError('Real spinal segment metadata required')
            if n.get('lane') not in LANES:
                raise ValueError('Real spinal neuron lane required')
    for e in edges:
        if not isinstance(e, dict) or e.get('source') not in ids or e.get('target') not in ids:
            raise ValueError('Synapse endpoints must exist')
        if not finite(e.get('weight'), -10, 10):
            raise ValueError('Finite excitatory/inhibitory weight required')
    return data
