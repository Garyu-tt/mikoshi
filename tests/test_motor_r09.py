"""Never turn retrospective physics QA into a live motor capability."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server.runtime import Runtime
from server import motor_registry, module_graph, graph_union


class MotorEvidenceTests(unittest.TestCase):
    def test_readonly_dynamic_actions_and_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Runtime(folder)
            actions=[c['id'] for c in r.capabilities]
            for report in motor_registry.discover():
                action='motor.calibration.'+report['id']+'.read'
                self.assertIn(action,actions)
                self.assertEqual(r.execute(action,{}),report)
            self.assertFalse(any('motor.actuate' in x for x in actions))
            self.assertIn('arch:mikoshi.motor.r185_lateral_z',
                 {x['id'] for x in graph_union.build(r)['nodes']})

    def test_experiments_are_distinct(self):
        cases={x['id']:x for x in motor_registry.discover()}
        self.assertEqual(len(cases),2)
        z=cases['r185_lateral_z']
        self.assertEqual(z['provenance']['kind'],'user_report')
        self.assertFalse(z['provenance']['independently_replayed'])
        samples={x['torque_n_m']:x for x in z['observations']}
        self.assertAlmostEqual(samples[-2]['velocity_right_m_s']-samples[0]['velocity_right_m_s'],.132)
        self.assertAlmostEqual(samples[2]['velocity_right_m_s']-samples[0]['velocity_right_m_s'],-.128)
        self.assertNotEqual(cases['r185_contact_x_20261017']['provenance']['kind'],z['provenance']['kind'])

    def test_no_action_when_evidence_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(motor_registry,'EVIDENCE',Path(folder)):
                r=Runtime(folder)
            self.assertFalse([c for c in r.capabilities if c['id'].startswith('motor.calibration.')])

    def test_reject_invalid_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'bad.json'
            file.write_text('{"schema":"mikoshi.motor-calibration.v1"}')
            with patch.object(motor_registry,'EVIDENCE',Path(folder)):
                with self.assertRaises(ValueError): motor_registry.discover()
