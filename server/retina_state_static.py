"""Immutability gate: checkpoint cannot rewrite identity of source anatomy."""
from array import array
import hmac
import numpy as np

IMMUTABLE = {
    'retina.type_map', 'retina._map', 'retina._fovea',
    'retina._counts', 'retina._lut', 'retina.foveal_positions',
    'sensor.receptor_lut', 'circuit._fovea', 'circuit._current_mosaic',
}


def ensure_original(dest, decoded):
    """Require unchanged cell identities and geometry in source-pinned retina."""
    for name in IMMUTABLE & decoded.keys():
        original, restored = dest[name], decoded[name]
        if isinstance(original, np.ndarray):
            if original.dtype != restored.dtype or original.shape != restored.shape:
                raise ValueError('Retinal anatomical array shape changed: ' + name)
            lhs, rhs = original.tobytes(), restored.tobytes()
        elif isinstance(original, array):
            if original.typecode != restored.typecode:
                raise ValueError('Retinal anatomical array type changed: ' + name)
            lhs, rhs = original.tobytes(), restored.tobytes()
        else:
            lhs, rhs = bytes(original), bytes(restored)
        if not hmac.compare_digest(lhs, rhs):
            raise ValueError('Checkpoint attempts to change retinal anatomy: ' + name)
