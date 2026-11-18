"""Neural checkpoint rejects nonfinite values even if hashes were rewritten."""
from array import array
import hashlib
import math
import unittest
import numpy as np
from server.retina_state_codec import pack, prepare


class NonfiniteNeuronsTest(unittest.TestCase):
    def test_reject_nan_float_array_capture(self):
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            pack('retina.h', array('f', [1., float('nan')]))

    def test_reject_infinite_numpy_capture(self):
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            pack('circuit.buffer', np.asarray([1., float('inf')]))

    def test_reject_rehashed_nan_on_restore_without_mutation(self):
        target = array('f', [3., 4.])
        forged = array('f', [3., float('nan')])
        raw = forged.tobytes()
        meta = {'kind':'array', 'typecode':'f', 'length':2,
                'itemsize':target.itemsize,'endian':'little',
                'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            prepare(target, meta, raw)
        self.assertEqual(list(target), [3., 4.])

    def test_reject_rehashed_infinite_numpy_without_mutation(self):
        target = np.asarray([3., 4.], dtype='<f8')
        forged = np.asarray([3., -float('inf')], dtype='<f8')
        raw = forged.tobytes()
        meta = {'kind':'numpy','dtype':forged.dtype.str, 'shape':[2],
                'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            prepare(target, meta, raw)
        self.assertEqual(target.tolist(), [3., 4.])
