"""IDE capability wiring exercised only with explicit test doubles."""
import os
import tempfile
import unittest
from unittest.mock import patch
from retina_fixture_r07 import fake_eye, blank_eye
from server.runtime import Runtime
from server.graph_union import build


class R239ActionsTests(unittest.TestCase):
    def test_unavailable_retina_has_no_executable_buttons(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{'MIKOSHI_RETINA_LEGACY_DIR':''}):
                rt=Runtime(tmp)
            self.assertFalse(any(n.startswith('engram.retina.r239.')
                                 for n in rt.handlers))
            self.assertFalse(any(n.startswith('visual2d.open.retina.axons.')
                                 for n in rt.handlers))

    def test_api_engram_roundtrip_and_dynamic_2d_registration(self):
        source={'original': 'a'*64}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{'MIKOSHI_RETINA_LEGACY_DIR':'/verified'}), \
                 patch('server.retina_caps.SparseRetinaR239',side_effect=[fake_eye(),blank_eye()]), \
                 patch('server.retina_state.source_hashes',return_value=source):
                rt=Runtime(tmp)
                self.assertIn('retina.r239.spikes.read',rt.handlers)
                self.assertIn('visual2d.open.retina.axons.left',rt.handlers)
                self.assertIn('engram.retina.r239.snapshot',rt.handlers)
                self.assertIn('view2d:retina.axons.left',
                              {n['id'] for n in build(rt)['nodes']})
                out=rt.execute('engram.retina.r239.snapshot',{'name':'fake'})
                self.assertTrue(out['state_present'])
                rt2=Runtime(tmp+'/second')
                rt2.vault=rt.vault
                restored=rt2.execute('engram.retina.r239.restore',
                                     {'filename':'fake.engram'})
                self.assertEqual(restored['last_step'],1)
                self.assertTrue(restored['restored'])
