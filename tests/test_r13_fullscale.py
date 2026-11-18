"""R13 source-resolved full resolution benchmark is explicit and bounded."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from smoke_r239_fullscale_r13 import run


class FullscaleTests(unittest.TestCase):
    def test_bad_parameter_fails_without_instantiating_neurons(self):
        cases = [dict(width=0), dict(before=3), dict(after=1),
                 dict(passes=3), dict(before=201, after=10),
                 dict(width=True)]
        with patch('smoke_r239_fullscale_r13.SparseRetinaR239') as engine:
            for options in cases:
                with self.subTest(options=options):
                    with self.assertRaises(ValueError):
                        run('/source-not-touched', **options)
            engine.assert_not_called()


class EvidenceGraphTests(unittest.TestCase):
    def test_fullscale_history_and_sparse_packet_are_not_invented_actuators(self):
        from server.module_graph import build
        graph = build()
        nodes = {x['id']: x for x in graph['nodes']}
        self.assertEqual(nodes['mikoshi.retina.r239.fullscale-evidence']['type'],
                         'evidence')
        self.assertIn('mikoshi.retina.r238.packet-transport', nodes)
        self.assertTrue(all(e['source'] in nodes and e['target'] in nodes
                            for e in graph['edges']))

    def test_packet_action_only_when_original_retina_is_present(self):
        import os
        import tempfile
        from server.runtime import Runtime
        from retina_fixture_r07 import blank_eye
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {'MIKOSHI_RETINA_LEGACY_DIR': ''}):
                without = Runtime(tmp)
            self.assertNotIn('retina.r239.photon.accept', without.handlers)
            with patch.dict(os.environ, {'MIKOSHI_RETINA_LEGACY_DIR': '/verified'}), \
                 patch('server.retina_caps.SparseRetinaR239', return_value=blank_eye()):
                with_it = Runtime(tmp)
            self.assertIn('retina.r239.photon.accept', with_it.handlers)


class CompleteSourceGraphTests(unittest.TestCase):
    def test_documentation_is_also_context_indexed(self):
        from server.codemap import graph
        ids = {x['id'] for x in graph()['nodes']}
        self.assertIn('file:docs/retina_r13.md', ids)
        self.assertIn('file:server/retina_packet.py', ids)
        self.assertIn('file:contracts/retina.photon_packet.v1.json', ids)
