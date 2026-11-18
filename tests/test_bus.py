import unittest
from server.bus import NeuralBus


class BusTests(unittest.TestCase):
    def test_preserves_order_and_observation_time(self):
        bus = NeuralBus(2)
        self.assertEqual(bus.publish('left-eye', 'optic.spikes', 1, 100, {'n': 3}, 'unix-ns')['event_id'], 1)
        with self.assertRaises(ValueError):
            bus.publish('left-eye', 'optic.spikes', 1, 200, {'n': 4}, 'unix-ns')
        bus.publish('left-eye', 'optic.spikes', 2, 300, {'n': 5}, 'unix-ns')
        bus.publish('left-eye', 'optic.spikes', 3, 400, {'n': 6}, 'unix-ns')
        result = bus.read(after=1)
        self.assertFalse(result['overrun'])
        self.assertEqual(result['items'][0]['sample_at_ns'], 300)
        self.assertEqual(result['newest_id'], 3)

    def test_detects_lost_events(self):
        bus = NeuralBus(1)
        for x in range(1, 4):
            bus.publish('s', 'ray', x, x * 10, {'x': x}, 'monotonic-ns')
        self.assertTrue(bus.read(after=1)['overrun'])
        self.assertFalse(bus.stats()['physical_motor_link'])

    def test_runtime_bus_capability_is_callable(self):
        import tempfile
        from server.runtime import Runtime
        with tempfile.TemporaryDirectory() as root:
            rt = Runtime(root)
            now = 1700000000000000000
            r = rt.execute('nervous.publish', {'source': 'test.eye', 'topic': 'optic.spikes',
                'source_sequence': 0, 'at_ns': now, 'clock_domain': 'unix-ns',
                'payload': {'spikes': 2}})
            self.assertTrue(r['accepted'])
            found = rt.execute('nervous.read', {})['items']
            self.assertEqual(found[0]['payload']['spikes'], 2)
