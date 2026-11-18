"""Exact optic stream and real event-bus reference, without fabricated light."""
import base64
import hashlib
import struct
import threading
import unittest
from types import SimpleNamespace
from server.spike_store import SpikeStore
from server.bus import NeuralBus
from server.retina_sparse import sparse_step, SparseRetinaR239


class SpikesTests(unittest.TestCase):
    def test_chunked_unsigned_uid_spikes_lossless(self):
        store=SpikeStore(max_packets=2,max_bytes=24)
        raw=struct.pack('<IIII',100,500,200,1500)
        desc=store.put(0,raw)
        self.assertTrue(desc['retained'])
        parts=[]
        offset=0
        while True:
            block=store.read({'sequence':0,'offset':offset,'limit':3})
            parts.append(base64.b64decode(block['raw_b64']))
            offset=block['next_offset']
            if block['done']:
                break
        self.assertEqual(b''.join(parts),raw)
        self.assertEqual(desc['sha256'],hashlib.sha256(raw).hexdigest())
        store.put(1,bytes(8));store.put(2,bytes(8))
        with self.assertRaisesRegex(ValueError,'expired'):
            store.read({'sequence':0})
        with self.assertRaises(ValueError):store.put(3,b'not-aligned')
        store.clear();self.assertEqual(store.used,0)

    def test_packet_published_with_reference_and_truthful_count(self):
        raw=struct.pack('<II',123,4321)
        class Eye:
            def step(self,args):
                return {'_spikes_raw':raw,'metadata':{'real_fresh_receptors':64},
                        'source_sequence':0,'sample_at_ns':100000,
                        'spike_bytes':len(raw),
                        'spikes_sha256':hashlib.sha256(raw).hexdigest()}
        rt=SimpleNamespace(sparse=Eye(),spike_store=SpikeStore(),bus=NeuralBus())
        result=sparse_step(rt,{})
        self.assertTrue(result['stream']['retained'])
        event=rt.bus.read()['items'][0]
        self.assertEqual(event['topic'],'optic.spikes.packet')
        self.assertEqual(event['payload']['count'],1)
        self.assertEqual(event['payload']['uid_encoding'],
                         'little-endian-uint32-uid-uint32-offset-us')
        self.assertEqual(base64.b64decode(rt.spike_store.read({'sequence':0})['raw_b64']),raw)

    def test_source_class_must_supply_r188_neural_methods(self):
        class FakeR188:
            def __init__(self, width, height):
                self.width,self.height=width,height
            def _view(self,name):pass
        class Sampler:
            def __init__(self, width, height, passes):pass
            def tile_ids(self, epoch, phase):return []
        class Circuit:
            def __init__(self,retina,sampler,body):
                self.retina=retina
        from unittest.mock import patch
        modules={'neural_retina_r188':SimpleNamespace(FastNeuralRetinaR188=FakeR188),
            'tile_sampler_r238':SimpleNamespace(ClusteredRetinalSamplerR238=Sampler),
            'clustered_retinal_circuit_r239':SimpleNamespace(ClusteredRetinalCircuitR239=Circuit)}
        with patch('server.retina_sparse.load',return_value=modules):
            eye=SparseRetinaR239('/verified',width=16,height=16)
        self.assertIsInstance(eye.retina,FakeR188)
        self.assertIsInstance(eye.sampler,Sampler)
        self.assertEqual(eye.source_folder,'/verified')
        self.assertTrue(callable(eye.retina._view))
