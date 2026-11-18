"""Load only verified historical modules in dependency order, opt-in."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PINS = Path(__file__).resolve().parent.parent / 'heritage/retina_source_pins.json'
DEPENDS = ('retina_r180.py', 'neural_retina_r182.py',
           'neural_retina_r188.py', 'staggered_retina_r228.py',
           'tile_sampler_r238.py', 'clustered_retinal_circuit_r239.py')


def verify_dir(folder):
    path = Path(folder).resolve(strict=True)
    pins = json.loads(PINS.read_text(encoding='utf-8'))['files']
    for name in DEPENDS:
        file = path / name
        if not file.is_file() or file.resolve().parent != path:
            raise ValueError('Missing verified retina dependency: ' + name)
        if hashlib.sha256(file.read_bytes()).hexdigest() != pins[name]:
            raise ValueError('Retina checksum mismatch: ' + name)
    return path


def load(folder):
    path = verify_dir(folder)
    # Historical imports use flat names. Refuse collisions with any other app.
    for filename in DEPENDS:
        name = filename[:-3]
        if name in sys.modules:
            source = getattr(sys.modules[name], '__file__', '')
            if not source or Path(source).resolve() != path / filename:
                raise ValueError('Legacy module namespace collision: ' + name)
    import numpy  # noqa: F401, required by genuine sparse retina
    result = {}
    for filename in DEPENDS:
        name = filename[:-3]
        if name not in sys.modules:
            spec = importlib.util.spec_from_file_location(name, path / filename)
            if spec is None or spec.loader is None:
                raise ImportError('Cannot load pinned source: ' + name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                del sys.modules[name]
                raise
        result[name] = sys.modules[name]
    return result
