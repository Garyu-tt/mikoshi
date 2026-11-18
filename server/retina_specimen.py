"""Save and recover actual R239 dynamic eye-state under strict source pins."""
import json
import re
from zipfile import ZipFile
from server import engram, retina_state

SAFE = re.compile(r'^[A-Za-z0-9_.-]{1,90}$')
KEY = 'neural/retina/state.json'


def snapshot(runtime, args):
    name = args.get('name')
    if not isinstance(name,str) or not SAFE.fullmatch(name):
        raise ValueError('Invalid retinal specimen name')
    eye = runtime.sparse
    if eye is None:
        raise ValueError('Original R239 retina is not connected')
    blobs = retina_state.capture(eye)
    dest = runtime.vault / (name + '.engram')
    if dest.exists():
        raise ValueError('Never overwrite an existing neural specimen')
    engram.create(dest, blobs, kind='retina-specimen', identity=str(eye.body))
    return {'created':dest.name, **engram.verify(dest),
            'engine':'genuine-r238-r239','state':'photoreceptors_and_retinal_circuit'}


def recover(runtime, args):
    name = args.get('filename')
    if not isinstance(name,str) or not SAFE.fullmatch(name) or not name.endswith('.engram'):
        raise ValueError('Invalid retinal specimen filename')
    eye = runtime.sparse
    if eye is None:
        raise ValueError('Original R239 retina is not connected')
    dest = runtime.vault/name
    meta = engram.verify(dest)
    if meta['kind'] != 'retina-specimen':
        raise ValueError('Engram is not a restorable R239 specimen')
    with ZipFile(dest) as archive:
        state = json.loads(archive.read(KEY))
        if meta.get('identity') != state.get('body_uuid'):
            raise ValueError('Engram identity differs from source neural body')
        return retina_state.restore(eye,state,archive)


def preflight(runtime, args):
    """Read-only validation against a pristine runtime with same source pins."""
    name=args.get('filename')
    if not isinstance(name,str) or not SAFE.fullmatch(name) or not name.endswith('.engram'):
        raise ValueError('Invalid retinal specimen filename')
    eye=runtime.sparse
    if eye is None:
        raise ValueError('Original R239 retina is not connected')
    archive_path=runtime.vault/name
    metadata=engram.verify(archive_path)
    if metadata['kind']!='retina-specimen':
        raise ValueError('Not a retinal specimen')
    from server.retina_sparse import SparseRetinaR239
    pristine=SparseRetinaR239(eye.source_folder,eye.width,eye.height,eye.passes)
    with ZipFile(archive_path) as archive:
        state=json.loads(archive.read(KEY))
        if metadata.get('identity')!=state.get('body_uuid'):
            raise ValueError('Engram identity differs from neural body')
        return retina_state.preflight(pristine,state,archive)
