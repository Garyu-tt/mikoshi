import tempfile
import unittest
from server.runtime import Runtime


class SnapshotTests(unittest.TestCase):
    def test_research_snapshot_is_honest_and_verifiable(self):
        with tempfile.TemporaryDirectory() as path:
            rt=Runtime(path)
            rt.execute('layout.create_tab',{'title':'Периферия'})
            saved=rt.execute('engram.snapshot_research', {'name':'retina-r03'})
            self.assertTrue(saved['valid'])
            self.assertFalse(saved['state_present'])
            self.assertEqual(saved['kind'],'research')
            self.assertIn('retina-r03.engram',rt.execute('engram.list',{})['engrams'])
            with self.assertRaises(ValueError):
                rt.execute('engram.snapshot_research', {'name':'retina-r03'})
