import copy
import unittest
from server.visual2d_validate import check
from server.visual2d_layout import project


class ContractTests(unittest.TestCase):
    def sample(self, organ='brain', projection='topology'):
        return {'schema':'mikoshi.visual2d.v1', 'id':'test.organ', 'organ':organ,
                'projection':projection, 'coordinate_kind':'derived',
                'source':{'id':'test.fixture'},
                'nodes':[{'id':'n1'}, {'id':'n2'}],
                'edges':[{'source':'n1','target':'n2'}]}

    def test_brain_connectome_flattened_deterministically(self):
        view = check(self.sample())
        one, two = project(view), project(view)
        self.assertEqual(one, two)
        self.assertEqual(len(one['nodes']), 2)
        self.assertTrue(all(0 <= n['x'] <= 1 for n in one['nodes']))
        self.assertEqual(one['layout_notice'], 'derived_2d_not_anatomical_position')

    def test_segmental_dorsal_ventral_lanes_are_not_3d(self):
        view = self.sample('spinal', 'segmental')
        view['nodes'][0].update(segment='C1',lane='sensory')
        view['nodes'][1].update(segment='C2',lane='motor')
        graph=project(check(view))
        self.assertLess(graph['nodes'][0]['x'], graph['nodes'][1]['x'])
        self.assertLess(graph['nodes'][0]['y'], graph['nodes'][1]['y'])

    def test_retina_refuses_invented_pixel_positions(self):
        view = self.sample('retina','retinotopic')
        with self.assertRaises(ValueError):project(check(view))

    def test_dangling_synapse_and_nonfinite_activity_rejected(self):
        view = self.sample()
        view['edges'][0]['target']='fabricated'
        with self.assertRaises(ValueError):check(view)
        view=self.sample();view['nodes'][0]['activity']=float('nan')
        with self.assertRaises(ValueError):check(view)

    def test_duplicate_ids_are_rejected(self):
        view=self.sample();view['nodes'][1]['id']='n1'
        with self.assertRaises(ValueError):check(view)
