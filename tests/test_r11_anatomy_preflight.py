"""Integrity gates: a valid checksum cannot authorize false retinal anatomy."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from retina_fixture_r07 import fake_eye, blank_eye
from server import engram, retina_state

PINS={'retina_r180.py':'a'*64,'tile_sampler_r238.py':'b'*64}
KEY='neural/retina/state.json'
FIELD='retina._lut'
PATH='neural/retina/buffers/'+FIELD+'.bin'


class RetinaImmutableAnatomyTest(unittest.TestCase):
    def setUp(self):
        patcher=patch('server.retina_state.source_hashes',return_value=PINS)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def checkpoint(self, edited=False):
        source=fake_eye()
        blobs=retina_state.capture(source)
        if edited:
            data=json.loads(blobs[KEY])
            raw=bytearray(blobs[PATH]);raw[0]^=1
            blobs[PATH]=bytes(raw)
            data['fields'][FIELD]['sha256']=hashlib.sha256(raw).hexdigest()
            blobs[KEY]=json.dumps(data,separators=(',',':')).encode()
        path=Path(self.temp.name)/'save.engram'
        engram.create(path,blobs,kind='retina-specimen',identity=str(source.body))
        return path

    def test_valid_preflight_is_read_only_then_restore(self):
        path=self.checkpoint()
        target=blank_eye()
        before=bytes(target.retina.photocurrent)
        with ZipFile(path) as z:
            state=json.loads(z.read(KEY))
            info=retina_state.preflight(target,state,z)
            self.assertTrue(info['accepted'])
            self.assertFalse(info['mutated'])
            self.assertEqual(target.last_step,-1)
            self.assertEqual(bytes(target.retina.photocurrent),before)
            info=retina_state.restore(target,state,z)
        self.assertTrue(info['restored'])
        self.assertEqual(target.last_step,1)
        self.assertEqual(target.circuit.sensor.last_step,1)

    def test_signed_but_wrong_anatomy_is_rejected_without_mutation(self):
        path=self.checkpoint(edited=True)
        target=blank_eye()
        before=bytes(target.retina.photocurrent)
        static=target.retina._lut.copy()
        with ZipFile(path) as z:
            state=json.loads(z.read(KEY))
            with self.assertRaisesRegex(ValueError,'anatomy'):
                retina_state.preflight(target,state,z)
            with self.assertRaisesRegex(ValueError,'anatomy'):
                retina_state.restore(target,state,z)
        self.assertEqual(target.last_step,-1)
        self.assertEqual(bytes(target.retina.photocurrent),before)
        self.assertTrue((target.retina._lut == static).all())

    def test_reject_inconsistent_archival_body_before_commit(self):
        path=self.checkpoint()
        target=blank_eye()
        original=target.body
        with ZipFile(path) as z:
            state=json.loads(z.read(KEY))
            state['body_uuid']='bad-uuid'
            with self.assertRaises(ValueError):
                retina_state.restore(target,state,z)
        self.assertEqual(original,target.body)
        self.assertEqual(target.last_step,-1)

    def test_preflight_rejects_old_schema_before_touching_engine(self):
        with self.assertRaisesRegex(ValueError,'schema'):
            retina_state.preflight(None,{'schema':'mikoshi.retina-r239-state.v1'},None)
