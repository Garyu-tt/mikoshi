"""Regression: old stride skipped real observed tiles; R05 aggregates them."""
import threading
import unittest
from types import SimpleNamespace
import numpy as np
from server.visual2d_retina import project


class RetinaLodTests(unittest.TestCase):
    def test_all_observations_survive_downsampling(self):
        w=h=32; per=w*h
        valid=np.zeros(per*2,dtype=np.bool_)
        timestamp=np.full(per*2,-1,dtype=np.int64)
        for x,y,ts in ((0,0,100),(24,24,110),(16,0,100),(31,31,110)):
            idx=y*w+x;valid[idx]=True;timestamp[idx]=ts
        sensor=SimpleNamespace(valid=valid,last_observed_ns=timestamp,
                               last_capture_ns=110)
        r=SimpleNamespace(width=w,height=h,retina=SimpleNamespace(tile=8),
            circuit=SimpleNamespace(sensor=sensor),body='test-fixture',
            last_step=1,lock=threading.Lock())
        for stride in (1,2,4):
            view=project(r,'left',stride)
            self.assertEqual(sum(n['sampled_receptors'] for n in view['nodes']),4)
            self.assertEqual(sum(n['fresh_receptors'] for n in view['nodes']),2)
            self.assertEqual(sum(n['receptor_capacity'] for n in view['nodes']) if stride==4
                else w*h, w*h)
        self.assertEqual(project(r,'right',4)['nodes'],[])
        self.assertEqual(len(project(r,'left',4)['nodes']),1)
        self.assertEqual(project(r,'left',4)['nodes'][0]['observed_fraction'],4/(w*h))
