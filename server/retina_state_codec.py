"""Explicit numeric-array codec. No pickle, executable objects or fake neurons."""
from array import array
import hashlib
import math
import re
import sys

FIELD = re.compile(r'^(retina|sensor|circuit)\.[A-Za-z_][A-Za-z_0-9]{0,79}$')
MAX_BUFFER = 128 * 1024 * 1024


def groups(engine):
    return {'retina': engine.retina, 'sensor': engine.circuit.sensor,
            'circuit': engine.circuit}


def buffers(engine):
    import numpy as np
    result = {}
    for group, obj in groups(engine).items():
        for key, val in vars(obj).items():
            if isinstance(val, (bytearray, array, np.ndarray)):
                result[group + '.' + key] = val
    return result


def pack(name, obj):
    import numpy as np
    if not FIELD.fullmatch(name):
        raise ValueError('Unsafe retinal state field')
    if isinstance(obj, bytearray):
        raw, meta = bytes(obj), {'kind': 'bytearray', 'length': len(obj)}
    elif isinstance(obj, array):
        if obj.typecode in ('f', 'd') and not all(map(math.isfinite, obj)):
            raise ValueError('Nonfinite neural state cannot be saved')
        raw = obj.tobytes()
        meta = {'kind':'array', 'typecode':obj.typecode, 'length':len(obj),
                'itemsize':obj.itemsize, 'endian':sys.byteorder}
    elif isinstance(obj, np.ndarray):
        if obj.dtype.hasobject or obj.dtype.kind not in ('u', 'i', 'b', 'f'):
            raise ValueError('Unsupported numpy retinal state dtype')
        if obj.dtype.kind == 'f' and not np.isfinite(obj).all():
            raise ValueError('Nonfinite neural state cannot be saved')
        raw = obj.tobytes(order='C')
        meta = {'kind':'numpy', 'dtype':obj.dtype.str, 'shape':list(obj.shape)}
    else:
        raise ValueError('Unsupported retinal buffer')
    if len(raw) > MAX_BUFFER:
        raise ValueError('Retinal field exceeds byte budget')
    meta['size'] = len(raw)
    meta['sha256'] = hashlib.sha256(raw).hexdigest()
    return raw, meta


def prepare(dest, meta, raw):
    """Validate completely before mutating a live numeric buffer."""
    import numpy as np
    if not isinstance(meta, dict) or len(raw) != meta.get('size') or (
            hashlib.sha256(raw).hexdigest() != meta.get('sha256')):
        raise ValueError('Retinal numeric data corrupt')
    kind = meta.get('kind')
    if kind == 'bytearray' and isinstance(dest, bytearray):
        if len(dest) == meta.get('length') == len(raw):
            return bytes(raw)
    if kind == 'array' and isinstance(dest, array):
        if (dest.typecode == meta.get('typecode') and dest.itemsize == meta.get('itemsize')
                and len(dest) == meta.get('length')):
            tmp = array(dest.typecode)
            tmp.frombytes(raw)
            if meta.get('endian') != sys.byteorder:
                tmp.byteswap()
            if tmp.typecode in ('f', 'd') and not all(map(math.isfinite, tmp)):
                raise ValueError('Nonfinite neural state cannot be restored')
            return tmp
    if kind == 'numpy' and isinstance(dest, np.ndarray):
        dtype = np.dtype(meta.get('dtype', 'O'))
        if (dest.flags.writeable and not dtype.hasobject and dtype.kind in ('u','i','b','f') and
                list(dest.shape) == meta.get('shape') and
                dest.dtype.kind == dtype.kind and dest.dtype.itemsize == dtype.itemsize):
            out = np.frombuffer(raw, dtype=dtype).reshape(dest.shape).astype(
                dest.dtype, copy=True)
            if out.dtype.kind == 'f' and not np.isfinite(out).all():
                raise ValueError('Nonfinite neural state cannot be restored')
            return out
    raise ValueError('Retinal numerical state type/shape mismatch')


def apply(dest, value):
    import numpy as np
    if isinstance(dest, bytearray):
        dest[:] = value
    elif isinstance(dest, array):
        dest[:] = value
    elif isinstance(dest, np.ndarray):
        dest[...] = value
    else:
        raise ValueError('Unknown retinal state destination')
