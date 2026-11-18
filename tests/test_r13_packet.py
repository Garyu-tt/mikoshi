"""Packet-only sensor transport is honest, bounded and source-ordered."""
import base64
import threading
import unittest
from types import SimpleNamespace
from server.retina_packet import ingest
from server.spike_store import SpikeStore
from server.bus import NeuralBus


class Sampler:
    def __init__(self):
        self.when = 1_780_000_000_000_000_000
        self.phase = 0
        self.decode_count = 0

    def decode(self, packet, body):
        self.decode_count += 1
        if packet != b'verified-phase' or body != 'true-body':
            raise ValueError('Invalid R238 packet source')
        return 0, self.phase, self.when, [10, 11], None


class Circuit:
    def __init__(self):
        self.sensor = SimpleNamespace(last_capture_ns=0)
        self.called = 0

    def accept(self, packet, frame_ms):
        self.called += 1
        self.sensor.last_capture_ns = 1_780_000_000_000_000_000
        return b'\x00' * 8, {'real_fresh_receptors': 2}


def fake_runtime():
    sampler, circuit = Sampler(), Circuit()
    eye = SimpleNamespace(width=16, height=16, passes=5,
        last_step=-1, body='true-body', sampler=sampler,
        circuit=circuit, lock=threading.RLock())
    return SimpleNamespace(sparse=eye, spike_store=SpikeStore(), bus=NeuralBus())


class PhotonPacketTest(unittest.TestCase):
    def setUp(self):
        self.runtime = fake_runtime()
        self.args = {'clock_domain':'unix-ns', 'frame_ms':33,
            'photon_packet_b64':base64.b64encode(b'verified-phase').decode()}

    def test_packet_publishes_real_bin_spikes_and_time(self):
        result = ingest(self.runtime, self.args)
        self.assertEqual(result['photon_transport'], 'r238-verified-sparse-phase')
        self.assertEqual(result['spike_bytes'], 8)
        self.assertEqual(result['source_sequence'], 0)
        self.assertTrue(result['stream']['retained'])
        self.assertEqual(self.runtime.bus.stats()['newest_id'], 1)
        self.assertEqual(self.runtime.sparse.circuit.called, 1)

    def test_bad_packet_never_mutates_neural_state(self):
        self.args['photon_packet_b64'] = base64.b64encode(b'tampered').decode()
        with self.assertRaisesRegex(ValueError, 'source'):
            ingest(self.runtime, self.args)
        self.assertEqual(self.runtime.sparse.last_step, -1)
        self.assertEqual(self.runtime.sparse.circuit.called, 0)

    def test_no_invented_or_duplicate_phases(self):
        ingest(self.runtime, self.args)
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            ingest(self.runtime, self.args)
        self.assertEqual(self.runtime.sparse.circuit.called, 1)

    def test_bounded_packet_and_strict_clock(self):
        for encoded in ('@@!', 'AAAA' * 4000):
            self.args['photon_packet_b64'] = encoded
            with self.assertRaises(ValueError):
                ingest(self.runtime, self.args)
        self.args['photon_packet_b64'] = base64.b64encode(b'verified-phase').decode()
        self.args['clock_domain'] = 'monotonic-ns'
        with self.assertRaisesRegex(ValueError, 'unix-ns'):
            ingest(self.runtime, self.args)
        self.assertEqual(self.runtime.sparse.last_step, -1)


if __name__ == '__main__':
    unittest.main()
