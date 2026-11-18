"""Genuine R228 photon phases -> original R239 clustered neural circuit."""
import base64
import binascii
import hashlib
import threading
import uuid
from server.retina_loader import load


class SparseRetinaR239:
    def __init__(self, folder, width=920, height=920, passes=5):
        parts = load(folder)
        self.source_folder = folder
        retina = parts['neural_retina_r188'].FastNeuralRetinaR188(
            width=width, height=height)
        sampler = parts['tile_sampler_r238'].ClusteredRetinalSamplerR238(
            width=width, height=height, passes=passes)
        if not callable(getattr(sampler, 'tile_ids', None)):
            raise ValueError('R239 requires R238 complete-microtile sampler')
        body = uuid.uuid4()
        circuit = parts['clustered_retinal_circuit_r239'].ClusteredRetinalCircuitR239(
            retina, sampler, body)
        self.retina, self.sampler, self.circuit = retina, sampler, circuit
        self.body, self.width, self.height = body, width, height
        self.passes, self.last_step = passes, -1
        self.lock = threading.Lock()

    def status(self):
        return {'active': True, 'engine': 'genuine-r238-r239',
                'dimensions': [self.width, self.height], 'eyes': 2,
                'phases': self.passes, 'last_step': self.last_step,
                'source_body_uuid': str(self.body),
                'photon_source': 'real_post_optical_rgb24_only',
                'checkpoint_format': 'mikoshi.retina-r239-state.v2',
                'checkpoint_contract_implemented': True,
                'original_roundtrip_verified': bool(getattr(self, '_roundtrip_verified', False)),
                'original_roundtrip_scope': 'this_process_32x32_four_phase_selftest',
                'stereo_r257_approved': False}

    def step(self, args):
        if not isinstance(args, dict):
            raise ValueError('Expected object')
        epoch, phase = args.get('epoch'), args.get('phase')
        if type(epoch) is not int or type(phase) is not int or not 0 <= phase < self.passes:
            raise ValueError('Invalid sample epoch/phase')
        when = args.get('sample_at_ns')
        if type(when) is not int or when <= 0:
            raise ValueError('Real sensor capture timestamp required')
        if args.get('clock_domain') != 'unix-ns':
            raise ValueError('R239 transport requires explicit unix-ns clock')
        frame_ms = args.get('frame_ms', 33)
        if type(frame_ms) is not int or not 1 <= frame_ms <= 250:
            raise ValueError('frame_ms must be 1..250')
        size = self.width * self.height * 3
        frames = []
        for side in ('left_rgb_b64', 'right_rgb_b64'):
            value = args.get(side)
            if not isinstance(value, str) or len(value) > 4 * ((size+2)//3):
                raise ValueError('RGB24 frame missing or too large')
            try:
                raw = base64.b64decode(value, validate=True)
            except binascii.Error as error:
                raise ValueError('Invalid RGB24 base64') from error
            if len(raw) != size:
                raise ValueError('Both post-optical eyes must be exact RGB24')
            frames.append(raw)
        with self.lock:
            step = epoch * self.passes + phase
            if step != self.last_step + 1:
                raise ValueError('Nonsequential sparse phase (no invented photons)')
            packet = self.sampler.packet(*frames, epoch, phase, when, self.body)
            spikes, metadata = self.circuit.accept(packet, frame_ms)
            self.last_step = step
        return {'_spikes_raw': spikes, 'metadata': metadata, 'source_sequence': step,
                'clock_domain': 'unix-ns', 'sample_at_ns': when,
                'spike_bytes': len(spikes),
                'spikes_sha256': hashlib.sha256(spikes).hexdigest(),
                'stream_truncated': False}


def publish(runtime, result):
    raw = result.pop('_spikes_raw')
    packet = runtime.spike_store.put(result['source_sequence'], raw)
    result.update({'stream': packet, 'spikes_b64': None,
                   'stream_truncated': not packet['retained']})
    runtime.bus.publish('retina.r239', 'optic.spikes.packet',
        result['source_sequence'], result['sample_at_ns'],
        {'spike_bytes': result['spike_bytes'], 'sha256': result['spikes_sha256'],
         'uid_encoding': 'little-endian-uint32-uid-uint32-offset-us',
         'count': result['spike_bytes']//8, 'stream': packet,
         'genuine_fresh_receptors': result['metadata'].get('real_fresh_receptors')},
        'unix-ns')
    return result


def sparse_step(runtime, args):
    return publish(runtime, runtime.sparse.step(args))
