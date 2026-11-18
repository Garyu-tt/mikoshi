"""Read build identity from release manifest, not static UI labels."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def metadata():
    info = json.loads((ROOT / 'RELEASE.json').read_text(encoding='utf-8'))
    version = info.get('release')
    if not isinstance(version, str) or not version.startswith('Mikoshi Connectome IDE '):
        raise ValueError('Invalid Mikoshi release metadata')
    return info


def version():
    return metadata()['release'].removeprefix('Mikoshi Connectome IDE ')
