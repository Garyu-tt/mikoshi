"""Opt-in full-resolution original R239 Engram v2 continuity benchmark.

Never runs from service startup or writes to a live neural instance.
Requires the pinned R180/R182/R188/R228/R238/R239 source tree and NumPy.
"""
import base64
import hashlib
import json
try:
    import resource  # POSIX-only; benchmark must import on Windows too.
except ImportError:
    resource = None
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

from server import engram, retina_state
from server.retina_sparse import SparseRetinaR239


def run(source, width=920, height=920, passes=5, before=7, after=13):
    if any(type(v) is not int for v in (width, height, passes, before, after)):
        raise ValueError('Integer dimensions and phase counts required')
    if before < passes or after < 2 or after + before > 200:
        raise ValueError('Must observe one complete field and compare >=2 phases')
    if passes not in (4, 5) or min(width, height) < 16:
        raise ValueError('Unsupported retinal sampling configuration')
    t0 = time.monotonic()
    eye = SparseRetinaR239(source, width, height, passes)
    created_s = round(time.monotonic() - t0, 3)
    reference_ns = 1_780_000_000_000_000_000
    image = {}
    for level in (0, 255, 80, 220):
        frame = bytes([level, level, level]) * (width * height)
        image[level] = base64.b64encode(frame).decode('ascii')

    def phase(engine, idx):
        level = (0, 255, 80, 220)[idx % 4]
        return engine.step({'epoch': idx // passes, 'phase': idx % passes,
            'sample_at_ns': reference_ns + idx * 33_000_000,
            'clock_domain': 'unix-ns', 'left_rgb_b64': image[level],
            'right_rgb_b64': image[level], 'frame_ms': 33})

    t = time.monotonic()
    for i in range(before):
        result = phase(eye, i)
        assert result['metadata']['whole_visual_field_not_updated_this_phase']
        assert not result['metadata']['image_reconstructed']
        assert 0 < result['metadata']['real_fresh_receptors'] < 2 * width * height
    observed = int(eye.circuit.sensor.valid.sum())
    if observed != 2 * width * height:
        raise AssertionError('Sampler failed to observe complete original field')
    with tempfile.TemporaryDirectory(prefix='mikoshi-r13-original-') as tmp:
        dest = Path(tmp) / 'fullsize-r239.engram'
        engram.create(dest, retina_state.capture(eye),
                      kind='retina-specimen', identity=str(eye.body))
        checksum = hashlib.sha256(dest.read_bytes()).hexdigest()
        verified = engram.verify(dest)
        if verified['kind'] != 'retina-specimen':
            raise AssertionError('Wrong Engram kind')
        restored = SparseRetinaR239(source, width, height, passes)
        with ZipFile(dest) as z:
            state = json.loads(z.read('neural/retina/state.json'))
            preflight = retina_state.preflight(restored, state, z)
            if not preflight['accepted'] or restored.last_step != -1:
                raise AssertionError('Preflight changed the neural engine')
            retina_state.restore(restored, state, z)
        total = 0
        hashes = hashlib.sha256()
        for i in range(before, before + after):
            continuous, recovered = phase(eye, i), phase(restored, i)
            if continuous['_spikes_raw'] != recovered['_spikes_raw']:
                raise AssertionError(f'Spikes diverged after restore on phase {i}')
            if continuous['metadata'] != recovered['metadata']:
                raise AssertionError(f'Metadata diverged on phase {i}')
            hashes.update(continuous['_spikes_raw'])
            total += continuous['spike_bytes'] // 8
        if total == 0:
            raise AssertionError('No optic spikes: stimulus lacks coverage')
        a, b = retina_state.capture(eye), retina_state.capture(restored)
        if a.keys() != b.keys() or any(a[k] != b[k] for k in a):
            raise AssertionError('Full neuronal state differs after recovery')
        elapsed_s = round(time.monotonic() - t, 3)
        return {'result': 'PASS', 'original_source_pinned': True,
            'resolution_per_eye': [width, height], 'receptors': 2 * width * height,
            'sampling_passes': passes, 'pre_checkpoint_phases': before,
            'post_checkpoint_matched_phases': after, 'post_checkpoint_spikes': total,
            'spike_trace_sha256': hashes.hexdigest(), 'neural_state_identical': True,
            'source_field_coverage': observed, 'engram_bytes': dest.stat().st_size,
            'engram_sha256': checksum, 'init_seconds': created_s,
            'experiment_seconds': elapsed_s,
            'rss_max_mib': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
            if resource is not None else None,
            'live_runtime_mutated': False, 'real_camera': False}

