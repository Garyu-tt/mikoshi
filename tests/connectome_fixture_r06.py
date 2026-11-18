"""Explicitly synthetic test topology for LIF integration tests."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server.runtime import Runtime

def dataset(organ='brain'):
    return {'schema':'mikoshi.connectome.v1','id':'labtest','organ':organ,
            'coordinate_kind':'derived','source':{'id':'unit-tests:synthetic'},
            'dt_ms':10,'neurons':[
                {'id':'n0','x':.2,'y':.2,'tau_ms':20,'threshold':1,
                 **({'segment':'C1','lane':'sensory'} if organ=='spinal' else {})},
                {'id':'n1','x':.8,'y':.8,'tau_ms':20,'threshold':1,
                 **({'segment':'C2','lane':'motor'} if organ=='spinal' else {})}],
            'synapses':[{'source':'n0','target':'n1','weight':1.25}]}


class ConnectomeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.dir=self.root/'models';self.dir.mkdir()
        self.name=self.dir/'labtest.connectome.json'
        self.environment=patch.dict(os.environ,{'MIKOSHI_CONNECTOME_DIR':str(self.dir),
            'MIKOSHI_VISUAL2D_DIR':str(self.root/'views'),
            'MIKOSHI_RETINA_R180':'','MIKOSHI_RETINA_LEGACY_DIR':''})
        self.environment.start();self.addCleanup(self.environment.stop)

    def write(self,model=None):
        self.name.write_text(json.dumps(dataset() if model is None else model))

    def runtime(self,name='state'):
        return Runtime(self.root/name)

    def step(self,rt,when,pulses=None):
        return rt.execute('connectome.step.labtest',{'sample_at_ns':when,
            'clock_domain':'monotonic-ns','pulses':pulses or {}})

