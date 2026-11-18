import tempfile
import unittest
from pathlib import Path
from server.retina_loader import verify_dir
from server.runtime import Runtime


class OriginalRetinaGate(unittest.TestCase):
    def test_source_hash_mandatory(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            for name in ('retina_r180.py','neural_retina_r182.py',
                         'staggered_retina_r228.py','clustered_retinal_circuit_r239.py'):
                (p/name).write_text('pass')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                verify_dir(temp)

    def test_no_fake_sparse_capability(self):
        with tempfile.TemporaryDirectory() as temp:
            rt=Runtime(temp)
            self.assertNotIn('retina.r239.step', rt.handlers)
            self.assertFalse(rt.execute('retina.sparse.status', {})['active'])
