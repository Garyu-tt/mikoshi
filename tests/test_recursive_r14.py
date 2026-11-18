"""Recursive assembly: containment, actual capabilities, toggles and contracts."""
import json
import tempfile
import unittest
from pathlib import Path
from server.runtime import Runtime
from server.recursive_catalog import Catalog


def manifest(path, ident, parent=None, kind='module', requires=None, provides=None):
    path.mkdir(parents=True, exist_ok=True)
    (path/'manifest.json').write_text(json.dumps({
        'schema':'adamantium.unit.v1','kind':kind,'id':ident,'parent':parent,
        'version':'1.0.0','provides':provides or [],'requires':requires or []}))


class RecursiveR14Tests(unittest.TestCase):
    def test_mikoshi_nested_graph_has_no_dangling_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Runtime(folder)
            graph = runtime.components.graph(runtime.visible_capabilities())
            ids = {n['id'] for n in graph['nodes']}
            actions = {c['id'] for c in runtime.visible_capabilities()}
            self.assertGreaterEqual(len(ids), 16)
            self.assertEqual(graph['unclaimed_actions'], [])
            self.assertTrue(all(e['source'] in ids and
                (e['target'] in ids or e['target'] in actions) for e in graph['edges']))
            self.assertTrue(any(e['relation']=='contains' for e in graph['edges']))
            self.assertEqual(runtime.execute('components.graph',{})['schema'],
                             'adamantium.recursive-graph.v1')

    def test_disable_leaf_hides_action_and_persists_without_dropping_neighbours(self):
        with tempfile.TemporaryDirectory() as folder:
            a = Runtime(folder)
            self.assertIn('nervous.stats', {c['id'] for c in a.visible_capabilities()})
            self.assertIn('research.search', {c['id'] for c in a.visible_capabilities()})
            a.execute('components.switch', {'unit':'mikoshi.neural','enabled':'false'})
            self.assertNotIn('nervous.stats', {c['id'] for c in a.visible_capabilities()})
            self.assertIn('research.search', {c['id'] for c in a.visible_capabilities()})
            with self.assertRaises(ValueError):a.execute('nervous.stats',{})
            b = Runtime(folder)
            self.assertNotIn('nervous.stats', {c['id'] for c in b.visible_capabilities()})
            b.execute('components.switch', {'unit':'mikoshi.neural','enabled':'true'})
            self.assertIn('nervous.stats', {c['id'] for c in b.visible_capabilities()})

    def test_protected_root_and_self_management(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Runtime(folder)
            for ident in ('mikoshi.connectome','mikoshi.ide.components'):
                with self.assertRaises(ValueError):
                    runtime.execute('components.switch', {'unit':ident,'enabled':'false'})

    def test_arbitrary_depth_and_no_ghosts(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);branch=p/'plugin'
            manifest(branch,'p.root',None,'plugin')
            for i in range(15):
                branch=branch/('level'+str(i))
                manifest(branch,'p.level.'+str(i), 'p.root' if i==0 else
                    'p.level.'+str(i-1), 'component', provides=[{
                        'name':'test.cap','version':'1.0.0','action':'never.loaded'}]
                    if i==14 else [])
            registry=Catalog(p,p/'settings.json')
            live=[{'id':'unclaimed.action'}]
            self.assertEqual(len(registry.graph(live)['nodes']),16)
            self.assertIsNone(registry.provider(live, {'name':'test.cap'}))
            self.assertEqual(registry.actions(live), [])
            self.assertEqual(registry.graph(live)['unclaimed_actions'], ['unclaimed.action'])



if __name__ == '__main__':unittest.main()
