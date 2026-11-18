"""Original R239 adversarial checkpoint tests, no live neural state mutation."""
import copy
import hashlib
import json
import os
from server import retina_state
from server.retina_sparse import SparseRetinaR239
from server.retina_state_codec import pack


class MemoryArchive:
    def __init__(self, blobs):
        self.blobs = blobs

    def read(self, name):
        return self.blobs[name]


def rejected(eye, state, blobs):
    dest = SparseRetinaR239(eye.source_folder, 32, 32, 4)
    before = retina_state.capture(dest)
    try:
        retina_state.preflight(dest, state, MemoryArchive(blobs))
    except ValueError:
        assert retina_state.capture(dest) == before, 'Invalid preflight altered eye'
        return True
    raise AssertionError('Corrupted Engram state was accepted')


def main():
    path = os.environ.get('MIKOSHI_RETINA_LEGACY_DIR')
    if not path:
        raise SystemExit('Genuine original R239 source required')
    eye = SparseRetinaR239(path, 32, 32, 4)
    # The time base is fixed because these are synthetic test observations.
    from server.retina_selftest import _phase
    for i in range(7):
        _phase(eye, i, 1_780_000_000_000_000_000)
    blobs = retina_state.capture(eye)
    state = json.loads(blobs['neural/retina/state.json'])
    baseline = SparseRetinaR239(path, 32, 32, 4)
    assert retina_state.preflight(baseline, state, MemoryArchive(blobs))['accepted']
    forged = copy.deepcopy(state)
    forged['source_sha256']['tile_sampler_r238.py'] = '0' * 64
    assert rejected(eye, forged, blobs)
    forged = copy.deepcopy(state)
    forged['scalars']['retina.frame_count'] += 1
    assert rejected(eye, forged, blobs)
    forged = copy.deepcopy(state)
    entries = blobs.copy()
    key = 'retina.type_map'
    name = 'neural/retina/buffers/' + key + '.bin'
    values = bytearray(entries[name]); values[0] = (values[0] + 1) % 4
    entries[name] = bytes(values)
    forged['fields'][key]['sha256'] = hashlib.sha256(values).hexdigest()
    assert rejected(eye, forged, entries)
    print(json.dumps({'result':'PASS','source_hash_tamper':True,
          'clock_tamper':True,'static_anatomy_tamper_with_rehashed_blob':True,
          'no_invalid_preflight_mutated_neurons':True}, sort_keys=True))


if __name__ == '__main__':
    main()
