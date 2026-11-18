"""The 2D optic plot must not invent points outside measured UID spikes."""
from array import array
import struct
import threading
import unittest
from types import SimpleNamespace
from server.visual2d_axons import project
from server.spike_store import SpikeStore


class AxonViewTests(unittest.TestCase):
    def test_verified_uid_coordinates_and_aggregated_spikes(self):
        retina = SimpleNamespace(pixels_per_eye=256,width=16,height=16,tile=8,
            tiles_x=2,tiles_y=2,tiles_per_eye=4,tile_count=8,
            pooled_ganglion_count=80,optic_ganglion_count=88,
            foveal_positions=array('I',[0,1,256,257]))
        eye = SimpleNamespace(retina=retina,lock=threading.RLock(),body='test')
        store = SpikeStore()
        self.assertEqual(project(eye,store,'left')['nodes'],[])
        raw=b''.join(struct.pack('<II',uid,i*100) for i,uid in
                     enumerate((0,1,20,40,80,84)))
        store.put(0,raw)
        left=project(eye,store,'left',1)
        right=project(eye,store,'right',1)
        self.assertEqual(left['spikes_in_eye'],4)
        self.assertEqual(right['spikes_in_eye'],2)
        self.assertEqual(sum(n['spike_count'] for n in left['nodes']),4)
        self.assertEqual(sum(n['spike_count'] for n in right['nodes']),2)
        self.assertTrue(all(n['activity'] <= 1 for n in left['nodes']))
        self.assertEqual(left['source']['kind'],'live_retinal_spikes')
        self.assertEqual(left['sample_sequence'],0)

    def test_invalid_original_uid_rejected_without_generated_neuron(self):
        retina=SimpleNamespace(pixels_per_eye=256,width=16,height=16,tile=8,
            tiles_x=2,tiles_y=2,tiles_per_eye=4,tile_count=8,
            pooled_ganglion_count=80,optic_ganglion_count=88,
            foveal_positions=array('I',[0,1,256,257]))
        eye=SimpleNamespace(retina=retina,lock=threading.RLock(),body='test')
        store=SpikeStore();store.put(0,struct.pack('<II',200,10))
        with self.assertRaisesRegex(ValueError,'Unknown original optic'):
            project(eye,store,'left')
