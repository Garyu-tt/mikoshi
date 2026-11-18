"""Export/recover a real, bounded LIF specimen, not Dante's full brain."""
import json
import re
import hashlib
from pathlib import Path
from zipfile import ZipFile
from server import engram
from server.connectome_state import capture, restore

SAFE = re.compile(r'^[A-Za-z0-9_.-]{1,90}$')
STATE = 'neural/connectome_state.json'
SOURCE = 'neural/connectome_source.json'


def snapshot(runtime, engine, args):
    name = args.get('name')
    if not isinstance(name,str) or not SAFE.fullmatch(name):
        raise ValueError('Invalid specimen name')
    state = capture(engine)
    blobs = {STATE:json.dumps(state,allow_nan=False,sort_keys=True).encode('utf8'),
             SOURCE:engine.source_bytes}
    path = runtime.vault / (name + '.engram')
    if path.exists():
        raise ValueError('Never overwrite an existing neural checkpoint')
    engram.create(path, blobs, kind='specimen', identity=engine.id)
    return {'created':path.name,**engram.verify(path),'engine':'cpu-lif-v1'}


def recover(runtime, engine, args):
    name = args.get('filename')
    if not isinstance(name,str) or not SAFE.fullmatch(name) or not name.endswith('.engram'):
        raise ValueError('Invalid Engram filename')
    path = runtime.vault / name
    meta = engram.verify(path)
    if meta['kind'] != 'specimen':
        raise ValueError('Cannot restore research Engram as neural state')
    with ZipFile(path) as z:
        if hashlib.sha256(z.read(SOURCE)).hexdigest() != engine.source_sha256:
            raise ValueError('Neural topology hash mismatch')
        if z.read(SOURCE) != engine.source_bytes:
            raise ValueError('Neural specimen source bytes differ')
        state = json.loads(z.read(STATE))
    return restore(engine,state)
