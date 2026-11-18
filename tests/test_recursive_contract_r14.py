"""Independent plugin resolution and rejection rules."""
import unittest
import tempfile
import json
from pathlib import Path
from server.recursive_catalog import Catalog
from tests.test_recursive_r14 import manifest

class RecursiveContractTests(unittest.TestCase):
    def test_optional_provider_and_required_gates(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            manifest(p/'alpha','test.alpha',None,'plugin',requires=[
                {'name':'storage.kv','minimum':'1.0.0','optional':True}])
            manifest(p/'alpha/worker','test.worker','test.alpha',provides=[{
                'name':'test.run','action':'test.run','version':'1.0.0'}],requires=[
                {'name':'storage.kv','minimum':'1.0.0','optional':False}])
            registry=Catalog(p,p/'settings.json')
            live=[{'id':'test.run'}]
            self.assertNotIn('test.run',[x['id'] for x in registry.actions(live)])
            self.assertTrue(registry.enabled(live)['test.alpha'])
            manifest(p/'database','test.database',None,'plugin',provides=[{
                'name':'storage.kv','action':'db.kv','version':'1.2.0'}])
            registry.reload()
            live.append({'id':'db.kv'})
            self.assertIn('test.run',[x['id'] for x in registry.actions(live)])
            selection=registry.provider(live, {'name':'storage.kv','minimum':'1.1.0'})
            self.assertEqual(selection['unit'],'test.database')
            self.assertIsNone(registry.provider(live, {'name':'storage.kv','minimum':'2.0.0'}))
            registry.switch('test.database',False)
            self.assertNotIn('test.run',[x['id'] for x in registry.actions(live)])

    def test_reject_child_misplacement_and_fictional_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);manifest(p/'alpha','parent.a',None,'plugin')
            manifest(p/'wrong','child.a','parent.a')
            with self.assertRaises(ValueError):Catalog(p,p/'state.json')
            (p/'wrong/manifest.json').unlink()
            manifest(p/'alpha/sub','child.a','parent.a')
            f=p/'alpha/sub/manifest.json';obj=json.loads(f.read_text())
            obj['isolation']='process';f.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):Catalog(p,p/'state.json')


if __name__ == '__main__':unittest.main()
