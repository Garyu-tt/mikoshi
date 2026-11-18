"""Read-only full state preflight, including pinned original anatomy."""
import hashlib
import json
import uuid
from server.retina_state_codec import buffers, prepare, groups
from server.retina_state_rules import validate
from server.retina_state_static import ensure_original

SCALARS = {'retina': ('last_frame_id','frame_count','_count_total'),
           'sensor': ('last_step','last_capture_ns')}
SCHEMA = 'mikoshi.retina-r239-state.v2'


def inspect(engine, state, archive):
    if not isinstance(state,dict) or state.get('schema') != SCHEMA:
        raise ValueError('Unknown retinal checkpoint schema')
    if engine.last_step != -1 or engine.circuit.sensor.last_step != -1:
        raise ValueError('Cannot overwrite an already-running retina')
    expected_geom=(engine.width,engine.height,engine.retina.tile,
                   engine.passes,engine.sampler.seed)
    given_geom=tuple(state.get(x) for x in ('width','height','tile','passes','seed'))
    if given_geom != expected_geom:
        raise ValueError('Retina geometry/sampling plan mismatch')
    validate(state)
    from server.retina_state import source_hashes
    pinned=source_hashes(engine)
    if pinned != state.get('source_sha256'):
        raise ValueError('Original retinal source hash mismatch')
    mosaic=json.dumps(engine.retina._type_count,
                      separators=(',',':')).encode('utf8')
    if hashlib.sha256(mosaic).hexdigest()!=state.get('static_type_counts_sha256'):
        raise ValueError('Original retinal mosaic differs')
    body=uuid.UUID(state['body_uuid'])
    dest=buffers(engine)
    fields=state.get('fields')
    if not isinstance(fields,dict) or fields.keys() != dest.keys():
        raise ValueError('Incomplete or unexpected retinal state fields')
    decoded={}
    for name,target in dest.items():
        key='neural/retina/buffers/'+name+'.bin'
        decoded[name]=prepare(target,fields[name],archive.read(key))
    ensure_original(dest,decoded)
    scalars=state.get('scalars')
    expected={g+'.'+k for g,names in SCALARS.items() for k in names}
    if not isinstance(scalars,dict) or scalars.keys()!=expected or any(
        type(v) is not int for v in scalars.values()):
        raise ValueError('Invalid checkpoint neuron counters')
    step=state['last_step']
    if step != scalars['sensor.last_step']:
        raise ValueError('R239 checkpoint phase mismatch')
    return {'decoded':decoded, 'dest':dest, 'scalars':scalars,
            'body':body, 'step':step}
