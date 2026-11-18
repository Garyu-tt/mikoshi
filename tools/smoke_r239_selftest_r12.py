"""Run live original source-pinned, isolated on-demand R239 self-test."""
import json
import os
from server.retina_sparse import SparseRetinaR239
from server.retina_selftest import run


def main():
    directory = os.environ.get('MIKOSHI_RETINA_LEGACY_DIR')
    if not directory:
        raise SystemExit('Real original retina source path required')
    eye = SparseRetinaR239(directory, width=32, height=32, passes=4)
    original = eye.status()
    assert not original['original_roundtrip_verified']
    result = run(eye)
    assert result['verified'] and eye.status()['original_roundtrip_verified']
    assert eye.last_step == -1
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
