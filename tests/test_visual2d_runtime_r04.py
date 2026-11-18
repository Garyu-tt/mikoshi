import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server.runtime import Runtime
from server.graph_union import build


class RuntimeViewsTests(unittest.TestCase):
    def fixture(self):
        return {'schema':'mikoshi.visual2d.v1', 'id':'brain.fixture',
                'organ':'brain','projection':'topology',
                'coordinate_kind':'derived','title':'Verified test input',
                'source':{'id':'tests:test_visual2d_runtime_r04'},
                'nodes':[{'id':'neuron.1'}, {'id':'neuron.2'}],
                'edges':[{'source':'neuron.1','target':'neuron.2'}]}

    def test_live_register_and_remove_no_fake_spinal(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)/'views';data.mkdir()
            with patch.dict(os.environ,{'MIKOSHI_VISUAL2D_DIR':str(data)}):
                runtime=Runtime(Path(tmp)/'state')
                self.assertEqual(runtime.execute('visual2d.list',{})['views'],[])
                self.assertFalse(any('visual2d.open.' in c['id'] for c in runtime.capabilities))
                path=data/'one.json';path.write_text(json.dumps(self.fixture()))
                runtime.update_views()
                action='visual2d.open.brain.fixture'
                self.assertIn(action,runtime.handlers)
                self.assertIn('view2d:brain.fixture', {n['id'] for n in build(runtime)['nodes']})
                result=runtime.execute(action,{})
                self.assertEqual(len(result['nodes']),2)
                self.assertEqual(len(result['edges']),1)
                path.unlink();runtime.update_views()
                self.assertNotIn(action,runtime.handlers)
                with self.assertRaises(ValueError):runtime.execute(action,{})

    def test_imported_view_persists_not_simulated(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)/'views';data.mkdir()
            payload=self.fixture();payload['organ']='spinal';payload['projection']='segmental'
            payload['nodes'][0].update(segment='C1',lane='sensory')
            payload['nodes'][1].update(segment='C1',lane='motor')
            (data/'spine.json').write_text(json.dumps(payload))
            with patch.dict(os.environ,{'MIKOSHI_VISUAL2D_DIR':str(data)}):
                runtime=Runtime(Path(tmp)/'state')
                self.assertEqual(runtime.execute('visual2d.list',{})['views'][0]['state'],
                                 'imported_read_only')
                self.assertFalse(runtime.bus.stats()['physical_motor_link'])
