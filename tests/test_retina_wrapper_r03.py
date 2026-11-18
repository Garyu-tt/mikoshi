import base64
import threading
import unittest
from server.retina_sparse import SparseRetinaR239


class FakeSensor:
    def packet(self, *args):
        return b'actual-source-test-double'


class FakeCircuit:
    def accept(self, packet, frame_ms):
        return b'\x00'*8, {'real_fresh_receptors': 12}


class SparseWrapperTests(unittest.TestCase):
    def test_adapter_order_and_real_frame_validation_using_doubles(self):
        engine=SparseRetinaR239.__new__(SparseRetinaR239)
        engine.width=16;engine.height=16;engine.passes=5
        engine.last_step=-1;engine.body='test-body'
        engine.sampler=FakeSensor();engine.circuit=FakeCircuit()
        engine.lock=threading.Lock()
        eye=base64.b64encode(bytes(16*16*3)).decode()
        args={'epoch':0,'phase':0,'sample_at_ns':1794960000123456789,
              'clock_domain':'unix-ns','left_rgb_b64':eye,'right_rgb_b64':eye}
        result=engine.step(args)
        self.assertEqual(result['metadata']['real_fresh_receptors'],12)
        self.assertEqual(result['source_sequence'],0)
        with self.assertRaisesRegex(ValueError,'Nonsequential'):
            engine.step(args)
        args['phase']=1;args['right_rgb_b64']='bad'
        with self.assertRaisesRegex(ValueError,'Invalid RGB24'):
            engine.step(args)
