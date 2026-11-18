import hashlib
import unittest
from server import codemap


class CodeMapTests(unittest.TestCase):
    def test_all_editable_files_fit_one_prompt(self):
        graph = codemap.graph()
        self.assertGreater(graph["total"], 20)
        self.assertTrue(all(n["bytes"] <= 5000 for n in graph["nodes"]))
        file = codemap.read("server/layout.py")
        self.assertEqual(file["sha256"], hashlib.sha256(file["content"].encode()).hexdigest())

    def test_no_traversal_and_graph_imports(self):
        with self.assertRaises(ValueError):
            codemap.read("../secret")
        graph = codemap.graph()
        self.assertTrue(any(e["target"] == "file:server/layout.py"
                            for e in graph["edges"]))
