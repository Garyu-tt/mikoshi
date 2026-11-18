import threading
import unittest
from types import SimpleNamespace
import numpy as np
from server.visual2d_retina import project


class RetinaProjectionTests(unittest.TestCase):
    def state(self):
        size = 16*16*2
        sensor = SimpleNamespace(valid=np.zeros(size, dtype=np.bool_),
                                 last_observed_ns=np.full(size,-1,dtype=np.int64),
                                 last_capture_ns=0)
        retina = SimpleNamespace(tile=8)
        circuit = SimpleNamespace(sensor=sensor)
        state = SimpleNamespace(width=16,height=16,retina=retina,
             body='test-source-id',circuit=circuit,last_step=-1,lock=threading.Lock())
        return state,sensor

    def test_empty_has_no_fake_vision(self):
        state,_=self.state();view=project(state,'left',1)
        self.assertEqual(view['nodes'],[])
        self.assertEqual(view['semantics'],'observed_receptor_density_not_irradiance')

    def test_real_sample_only_in_correct_eye(self):
        state,sensor=self.state();sensor.valid[0]=True;sensor.last_observed_ns[0]=1234;sensor.last_capture_ns=1234
        left=project(state,'left',1);right=project(state,'right',1)
        self.assertEqual(len(left['nodes']),1)
        self.assertEqual(right['nodes'],[])
        self.assertEqual(left['nodes'][0]['sampled_receptors'],1)
        self.assertEqual(left['nodes'][0]['last_observed_ns'],1234)
        self.assertEqual(left['nodes'][0]['observed_fraction'],1/64)

    def test_stride_bounds(self):
        state,_=self.state()
        for stride in (0,-1,33):
            with self.assertRaises(ValueError):project(state,'left',stride)
