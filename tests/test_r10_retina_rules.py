"""Reject inconsistent neuron clocks before touching an existing specimen."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from retina_fixture_r07 import fake_eye, blank_eye
from server import engram, retina_state
from server.retina_state_rules import validate

PINS={'retina_r180.py':'a'*64,'tile_sampler_r238.py':'b'*64}


class R10RetinaRulesTests(unittest.TestCase):
    def setUp(self):
        p=patch('server.retina_state.source_hashes',return_value=PINS)
        p.start(); self.addCleanup(p.stop)

    def test_original_clock_conventions(self):
        o=fake_eye()
        data=json.loads(retina_state.capture(o)['neural/retina/state.json'])
        self.assertIs(validate(data),data)
        self.assertEqual(data['scalars']['retina.frame_count'],data['last_step']+1)

    def test_reject_wrong_clock_before_buffer_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            orig=fake_eye()
            f=Path(folder)/'valid.engram'
            engram.create(f,retina_state.capture(orig),kind='retina-specimen',
                          identity=str(orig.body))
            target=blank_eye(); original=bytes(target.retina.photocurrent)
            with ZipFile(f) as z:
                baseline=json.loads(z.read('neural/retina/state.json'))
                for key,value in [('retina.last_frame_id',0),
                                  ('retina.frame_count',7),
                                  ('sensor.last_capture_ns',0)]:
                    bad=copy.deepcopy(baseline)
                    bad['scalars'][key]=value
                    with self.assertRaises(ValueError):
                        retina_state.restore(target,bad,z)
            self.assertEqual(bytes(target.retina.photocurrent),original)
            self.assertEqual(target.last_step,-1)

    def test_reject_bad_capture_before_serialization(self):
        o=fake_eye();o.retina.frame_count=999
        with self.assertRaisesRegex(ValueError,'counter'):
            retina_state.capture(o)

    def test_reject_phase_overflow(self):
        o=fake_eye()
        state=json.loads(retina_state.capture(o)['neural/retina/state.json'])
        state['last_step']=2**32*state['passes']
        state['scalars']['sensor.last_step']=state['last_step']
        state['scalars']['retina.last_frame_id']=state['last_step']+1
        state['scalars']['retina.frame_count']=state['last_step']+1
        with self.assertRaisesRegex(ValueError,'overflow'): validate(state)

class R10EngramSemanticTests(unittest.TestCase):
    def test_semantically_invalid_engram_rejected(self):
        from zipfile import ZipFile
        with patch('server.retina_state.source_hashes',return_value=PINS):
            specimen=fake_eye()
            blobs=retina_state.capture(specimen)
        key='neural/retina/state.json'
        data=json.loads(blobs[key])
        data['scalars']['retina.frame_count']+=1
        blobs[key]=json.dumps(data,sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.engram'
            with self.assertRaisesRegex(ValueError,'counter'):
                engram.create(path,blobs,kind='retina-specimen',identity=str(specimen.body))
            self.assertFalse(path.exists())
