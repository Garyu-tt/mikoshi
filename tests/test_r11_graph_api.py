"""Capabilities must reflect executable services, not decorative mock buttons."""
import tempfile
import unittest
from unittest.mock import patch
from server.runtime import Runtime
from server.graph_union import build
from server.module_graph import build as modules


class R11CapabilitiesTest(unittest.TestCase):
    def test_preflight_is_not_a_fake_capability_without_live_original(self):
        with patch.dict('os.environ',{'MIKOSHI_RETINA_LEGACY_DIR':''}):
            with tempfile.TemporaryDirectory() as tmp:
                r=Runtime(tmp)
                names={c['id'] for c in r.capabilities}
                self.assertNotIn('engram.retina.r239.preflight',names)
                self.assertNotIn('engram.retina.r239.restore',names)
                m=modules()
                self.assertIn('mikoshi.retina.engram.preflight',
                              {n['id'] for n in m['nodes']})
                graph=build(r)
                ids={n['id'] for n in graph['nodes']}
                self.assertIn('arch:mikoshi.retina.anatomy.guard',ids)
                self.assertNotIn('engram.retina.r239.preflight',ids)
                self.assertTrue(all(e['source'] in ids and e['target'] in ids
                                    for e in graph['edges']))
