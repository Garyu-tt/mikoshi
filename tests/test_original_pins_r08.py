"""The loader must refuse missing or changed historical code."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server import retina_loader


class PinsR08(unittest.TestCase):
    def test_all_six_sources_required_with_exact_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            pins = {}
            for name in retina_loader.DEPENDS:
                raw = ('# original fixture for ' + name + '\n').encode()
                (folder/name).write_bytes(raw)
                pins[name] = hashlib.sha256(raw).hexdigest()
            manifest = folder/'pins.json'
            manifest.write_text(json.dumps({'files': pins}))
            with patch('server.retina_loader.PINS', manifest):
                self.assertEqual(retina_loader.verify_dir(folder), folder.resolve())
                (folder/'tile_sampler_r238.py').write_text('changed original')
                with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                    retina_loader.verify_dir(folder)
                (folder/'tile_sampler_r238.py').unlink()
                with self.assertRaisesRegex(ValueError, 'Missing verified'):
                    retina_loader.verify_dir(folder)

    def test_live_gate_cannot_skip_original_tile_sampler(self):
        self.assertEqual(retina_loader.DEPENDS[-2:],
                         ('tile_sampler_r238.py','clustered_retinal_circuit_r239.py'))


if __name__ == '__main__':
    unittest.main()
