"""Measured Z torque sensitivity, deliberately non-actuating."""
import tempfile
import unittest
from server import motor_registry, graph_union
from server.motor_response import evaluate
from server.runtime import Runtime


class MotorR10Tests(unittest.TestCase):
    def test_physics_response_is_data_only(self):
        record=next(x for x in motor_registry.discover() if x['id']=='r185_lateral_z')
        result=evaluate(record)
        self.assertEqual(result['samples'],3)
        self.assertEqual(result['observed_torque_range_n_m'],[-2,2])
        self.assertAlmostEqual(result['segments'][0]['delta_v_per_n_m'],-.066)
        self.assertAlmostEqual(result['segments'][1]['delta_v_per_n_m'],-.064)
        self.assertTrue(result['both_feet_contact_for_each_reported_frame'])
        self.assertFalse(result['motor_command_available'])
        self.assertFalse(result['extrapolation_allowed'])
        self.assertFalse(result['provenance']['independently_replayed'])

    def test_fallback_for_other_protocol_is_absence_not_mock(self):
        other=next(x for x in motor_registry.discover() if 'contact_x' in x['id'])
        with self.assertRaisesRegex(ValueError,'No signed'):
            evaluate(other)
        with tempfile.TemporaryDirectory() as folder:
            rt=Runtime(folder)
            action='motor.calibration.r185_lateral_z.response'
            self.assertIn(action,rt.handlers)
            self.assertNotIn('motor.calibration.r185_contact_x_20261017.response',rt.handlers)
            self.assertFalse(any('motor.actuate' in key for key in rt.handlers))
            self.assertEqual(rt.execute(action,{})['samples'],3)
            g=graph_union.build(rt)
            self.assertIn(action,{n['id'] for n in g['nodes']})

    def test_reject_duplicate_or_nonfinite_sample(self):
        r=next(x for x in motor_registry.discover() if x['id']=='r185_lateral_z')
        import copy
        x=copy.deepcopy(r);x['observations'][0]['torque_n_m'] = 2
        with self.assertRaisesRegex(ValueError,'duplicate'): evaluate(x)
        x=copy.deepcopy(r);x['observations'][0]['velocity_right_m_s']=float('nan')
        with self.assertRaisesRegex(ValueError,'Invalid'): evaluate(x)
