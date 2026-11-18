import tempfile
import unittest
from server import graph_union, codemap
from server.runtime import Runtime


class UnifiedGraphTests(unittest.TestCase):
    def test_every_edge_has_existing_nodes(self):
        with tempfile.TemporaryDirectory() as temp:
            rt=Runtime(temp)
            graph=graph_union.build(rt)
            ids={n['id'] for n in graph['nodes']}
            self.assertEqual(len(ids), len(graph['nodes']))
            self.assertTrue(all(e['source'] in ids and e['target'] in ids
                                for e in graph['edges']))
            self.assertTrue(any(e['relation']=='implemented_in' for e in graph['edges']))
            self.assertTrue(any(n['id'].startswith('history:') for n in graph['nodes']))
            self.assertTrue(any(n['id'].startswith('arch:') for n in graph['nodes']))

    def test_frontend_modules_have_import_edges(self):
        code=codemap.graph()
        self.assertTrue(any(e['source']=='file:client/app.js' and
                            e['target']=='file:client/board.js' for e in code['edges']))
