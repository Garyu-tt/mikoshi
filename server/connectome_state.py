"""Strict, portable numeric checkpoint for the CPU LIF network."""
import json
from server.connectome_validate import finite

SCHEMA = 'mikoshi.connectome-state.v1'


def capture(engine):
    with engine.lock:
        return {'schema':SCHEMA,'id':engine.id,'source_sha256':engine.source_sha256,
                'tick':engine.tick,'sample_at_ns':engine.at_ns,
                'clock_domain':engine.clock_domain,
                'potentials':list(engine.potential),
                'refractory_ms':list(engine.refractory),
                'last_spikes':[engine.names[i] for i in engine.spikes]}


def validate(engine, state):
    if not isinstance(state, dict) or state.get('schema') != SCHEMA:
        raise ValueError('Incompatible neural-state schema')
    if state.get('id') != engine.id or state.get('source_sha256') != engine.source_sha256:
        raise ValueError('Engram topology identity/hash mismatch')
    n = len(engine.names)
    for key in ('potentials', 'refractory_ms'):
        seq = state.get(key)
        if not isinstance(seq, list) or len(seq) != n:
            raise ValueError('Neural state shape mismatch')
        if not all(finite(v, -1000, 1000) for v in seq):
            raise ValueError('Nonfinite or invalid neural state')
    if any(v < 0 for v in state['refractory_ms']):
        raise ValueError('Invalid refractory duration')
    tick, when = state.get('tick'), state.get('sample_at_ns')
    if type(tick) is not int or tick < 0 or type(when) is not int or when < 0:
        raise ValueError('Invalid clock checkpoint')
    domain = state.get('clock_domain')
    if domain not in ('unix-ns','monotonic-ns',None) or (tick > 0 and (when == 0 or domain is None)):
        raise ValueError('Incomplete clock checkpoint')
    spikes = state.get('last_spikes')
    if not isinstance(spikes, list) or len(spikes) > n or len(set(spikes)) != len(spikes):
        raise ValueError('Invalid last-spike population')
    if any(not isinstance(k,str) or k not in engine.by_id for k in spikes):
        raise ValueError('Unknown spike neuron')
    return True


def restore(engine, state):
    with engine.lock:
        validate(engine,state)
        if engine.tick:
            raise ValueError('Refuse to overwrite running neural state: use fresh runtime')
        engine.potential = [float(x) for x in state['potentials']]
        engine.refractory = [float(x) for x in state['refractory_ms']]
        engine.spikes = [engine.by_id[k] for k in state['last_spikes']]
        engine.tick = state['tick']
        engine.at_ns = state['sample_at_ns']
        engine.clock_domain = state['clock_domain']
        return {'restored':True,'id':engine.id,'tick':engine.tick,
                'source_sha256':engine.source_sha256}
