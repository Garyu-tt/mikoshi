"""Explicit, isolated source-pinned original R239 + Engram v2 self-test."""
import base64
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile
from server import engram, retina_state
from server.retina_sparse import SparseRetinaR239


def _phase(eye, index, timestamp):
    level = (0, 255, 80, 220)[index % 4]
    image = base64.b64encode(bytes([level] * 3) * (
        eye.width * eye.height)).decode('ascii')
    return eye.step({'epoch': index // eye.passes,
                     'phase': index % eye.passes,
                     'sample_at_ns': timestamp + index * 33_000_000,
                     'clock_domain': 'unix-ns',
                     'left_rgb_b64': image, 'right_rgb_b64': image,
                     'frame_ms': 33})


def run(active):
    """Test two independent originals. Do not mutate the active eye."""
    active._roundtrip_verified = False
    eye = SparseRetinaR239(active.source_folder, 32, 32, 4)
    time_base = 1_780_000_000_000_000_000
    for index in range(7):
        _phase(eye, index, time_base)
    with tempfile.TemporaryDirectory(prefix='mikoshi-r239-selftest-') as temp:
        archive_path = Path(temp) / 'isolated.engram'
        engram.create(archive_path, retina_state.capture(eye),
                      kind='retina-specimen', identity=str(eye.body))
        info = engram.verify(archive_path)
        restored = SparseRetinaR239(active.source_folder, 32, 32, 4)
        with ZipFile(archive_path) as archive:
            state = json.loads(archive.read('neural/retina/state.json'))
            preflight = retina_state.preflight(restored, state, archive)
            if not preflight['accepted'] or restored.last_step != -1:
                raise AssertionError('Preflight unexpectedly changed retina')
            retina_state.restore(restored, state, archive)
        count = 0
        for index in range(7, 20):
            a = _phase(eye, index, time_base)
            b = _phase(restored, index, time_base)
            if a['_spikes_raw'] != b['_spikes_raw'] or a['metadata'] != b['metadata']:
                raise AssertionError('R239 post-Engram neuron event divergence')
            count += len(a['_spikes_raw']) // 8
        if count <= 0 or retina_state.capture(eye) != retina_state.capture(restored):
            raise AssertionError('R239 neuron state or stimulus invalid')
        result = {'verified': True, 'format': 'retina-r239-state.v2',
                  'engine': 'source-pinned-original-r238-r239',
                  'test_resolution': [32, 32], 'phases_before': 7,
                  'phases_compared': 13, 'identical_spikes': count,
                  'original_active_eye_untouched': True,
                  'archive_verified': info['valid'],
                  'tested_archive_bytes': archive_path.stat().st_size}
    active._roundtrip_verified = True
    return result
