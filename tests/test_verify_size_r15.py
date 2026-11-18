"""The source-size gate must work on a real Git checkout."""
import tempfile
import unittest
from pathlib import Path
from tools.verify_size import oversized


class SourceBudgetTests(unittest.TestCase):
    def test_ignore_git_metadata_and_mandatory_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'.git'/'objects').mkdir(parents=True)
            (root/'.git'/'objects'/'packfile').write_bytes(b'x'*100000)
            (root/'LICENSE').write_bytes(b'GPL'*20000)
            (root/'server').mkdir()
            (root/'server'/'small.py').write_bytes(b'pass\n')
            self.assertEqual(oversized(root), [])

    def test_reject_actual_oversized_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'big.py').write_bytes(b'0'*5001)
            self.assertEqual(oversized(root), [('big.py', 5001)])


if __name__ == '__main__':
    unittest.main()
