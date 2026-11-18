"""Actual checkpoint codec tests with representative typed state, no fake capability."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
import numpy as np
from retina_fixture_r07 import fake_eye, blank_eye
from server import retina_state, engram

PINS = {'retina_r180.py':'a'*64, 'neural_retina_r188.py':'b'*64}


class R239CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.source = patch('server.retina_state.source_hashes',return_value=PINS)
        self.source.start()
        self.addCleanup(self.source.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'r239.engram'

    def make(self):
        original=fake_eye()
        blobs=retina_state.capture(original)
        engram.create(self.path,blobs,kind='retina-specimen',identity=str(original.body))
        return original

    def test_numeric_checkpoint_bytes_and_temporal_identity(self):
        original=self.make()
        self.assertTrue(engram.verify(self.path)['state_present'])
        second=blank_eye()
        with ZipFile(self.path) as z:
            state=json.loads(z.read('neural/retina/state.json'))
            result=retina_state.restore(second,state,z)
        self.assertTrue(result['restored'])
        self.assertEqual(second.body,original.body)
        self.assertEqual(second.circuit.sensor.expected_body,original.body)
        self.assertEqual(second.circuit.sensor.last_capture_ns,100)
        self.assertEqual(second.circuit.sensor.last_step,1)
        self.assertEqual(second.last_step,1)
        self.assertEqual(second.retina.photocurrent,original.retina.photocurrent)
        self.assertEqual(second.retina.horizontal,original.retina.horizontal)
        np.testing.assert_array_equal(second.circuit._old_mean,original.circuit._old_mean)
        np.testing.assert_array_equal(second.circuit.sensor.valid,original.circuit.sensor.valid)
        self.assertIsNone(second.sampler._epoch)
        with ZipFile(self.path) as z:
            with self.assertRaisesRegex(ValueError,'already-running'):
                retina_state.restore(second,state,z)

    def test_no_mutation_after_source_hash_or_buffer_failure(self):
        self.make()
        other=blank_eye()
        before=bytes(other.retina.photocurrent)
        with ZipFile(self.path) as z:
            state=json.loads(z.read('neural/retina/state.json'))
            with patch('server.retina_state.source_hashes',return_value={'bad':'0'*64}):
                with self.assertRaisesRegex(ValueError,'source hash'):
                    retina_state.restore(other,state,z)
            state['fields']['retina.baseline']['size'] += 1
            with self.assertRaisesRegex(ValueError,'numeric data'):
                retina_state.restore(other,state,z)
        self.assertEqual(bytes(other.retina.photocurrent),before)
        self.assertEqual(other.last_step,-1)

    def test_archive_rejects_research_mislabel_and_missing_buffer(self):
        original=self.make()
        with ZipFile(self.path) as z:
            state=json.loads(z.read('neural/retina/state.json'))
            blobs = {n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        wrong=Path(self.temp.name)/'wrong.engram'
        del blobs['neural/retina/buffers/retina.baseline.bin']
        with self.assertRaisesRegex(ValueError,'missing or unexpected'):
            engram.create(wrong,blobs,kind='retina-specimen',identity=str(original.body))
        self.assertFalse(wrong.exists())
        with self.assertRaisesRegex(ValueError,'neural'):
            engram.create(wrong,blobs,kind='research')
