"""Capture and restore original R239 continuous neural state."""
import hashlib
import json
from server.retina_state_codec import buffers, pack, apply, groups
from server.retina_state_rules import validate as validate_clocks
from server.retina_state_preflight import inspect, SCHEMA, SCALARS
from server.retina_loader import DEPENDS, verify_dir


def source_hashes(engine):
    path=verify_dir(engine.source_folder)
    return {n:hashlib.sha256((path/n).read_bytes()).hexdigest() for n in DEPENDS}


def capture(engine):
    with engine.lock:
        store={}; descriptor={}
        for name,item in sorted(buffers(engine).items()):
            raw,descriptor[name]=pack(name,item)
            store['neural/retina/buffers/'+name+'.bin']=raw
        scalars={}
        for group,names in SCALARS.items():
            obj=groups(engine)[group]
            for name in names:
                value=getattr(obj,name)
                if type(value) is not int:
                    raise ValueError('Invalid retinal scalar type')
                scalars[group+'.'+name]=value
        if scalars['sensor.last_step']!=engine.last_step:
            raise ValueError('R239 adapter/circuit phase mismatch')
        mosaic=json.dumps(engine.retina._type_count,
                          separators=(',',':')).encode('utf8')
        state={'schema':SCHEMA,'body_uuid':str(engine.body),
               'width':engine.width,'height':engine.height,
               'tile':engine.retina.tile,'passes':engine.passes,
               'seed':engine.sampler.seed,'last_step':engine.last_step,
               'scalars':scalars,'fields':descriptor,
               'static_type_counts_sha256':hashlib.sha256(mosaic).hexdigest(),
               'source_sha256':source_hashes(engine)}
        validate_clocks(state)
        store['neural/retina/state.json']=json.dumps(state,sort_keys=True,
                             allow_nan=False,separators=(',',':')).encode('utf8')
        return store


def preflight(engine,state,archive):
    """Never changes the engine, even if the archive is invalid."""
    if not isinstance(state,dict) or state.get('schema') != SCHEMA:
        raise ValueError('Unknown retinal checkpoint schema')
    with engine.lock:
        p=inspect(engine,state,archive)
        return {'accepted':True,'last_step':p['step'],
                'source_body_uuid':str(p['body']),
                'numeric_fields':len(p['decoded']),
                'anatomy_guard':'source_match','mutated':False}


def restore(engine,state,archive):
    if not isinstance(state,dict) or state.get('schema') != SCHEMA:
        raise ValueError('Unknown retinal checkpoint schema')
    with engine.lock:
        p=inspect(engine,state,archive)
        for name,value in p['decoded'].items():
            apply(p['dest'][name],value)
        for name,value in p['scalars'].items():
            group,field=name.split('.',1)
            setattr(groups(engine)[group],field,value)
        engine.body=p['body']
        engine.circuit.sensor.expected_body=p['body']
        engine.sampler._epoch=None
        engine.sampler._phase_map=None
        engine.sampler._ids=None
        engine.last_step=p['step']
        return {'restored':True,'last_step':p['step'],
                'source_body_uuid':str(p['body']),
                'numeric_fields':len(p['decoded']),
                'engine':'genuine-r238-r239'}
