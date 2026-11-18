"""Only verified original-source runtime may offer an explicit live self-test."""
import os
import tempfile
import unittest
from unittest.mock import patch
from server.runtime import Runtime


class SelftestCapabilityTest(unittest.TestCase):
    def test_absent_without_original_retina(self):
        with patch.dict(os.environ, {'MIKOSHI_RETINA_LEGACY_DIR': ''}):
            with tempfile.TemporaryDirectory() as tmp:
                r = Runtime(tmp)
                self.assertNotIn('engram.retina.r239.selftest', r.handlers)

    def test_present_if_genuine_loader_succeeds(self):
        from retina_fixture_r07 import blank_eye
        eye = blank_eye()
        with patch.dict(os.environ, {'MIKOSHI_RETINA_LEGACY_DIR': '/verified'}), \
                patch('server.retina_caps.SparseRetinaR239', return_value=eye):
            with tempfile.TemporaryDirectory() as tmp:
                r = Runtime(tmp)
                self.assertIn('engram.retina.r239.selftest', r.handlers)
                self.assertIn('engram.retina.r239.selftest',
                              {n['id'] for n in r.capabilities})

    def test_anatomy_test_evidence_is_not_fake_capability(self):
        from server.module_graph import build
        graph = build()
        ids = {n['id'] for n in graph['nodes']}
        self.assertIn('mikoshi.retina.r239.selftest', ids)
        self.assertIn('mikoshi.retina.r239.verified-evidence', ids)
        self.assertTrue(all(e['source'] in ids and e['target'] in ids
                            for e in graph['edges']))
