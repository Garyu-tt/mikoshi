"""Adversarial checks for recursive lifecycle and dynamic capability access."""
import json
import tempfile
import unittest
from pathlib import Path
from server.runtime import Runtime
from server.recursive_catalog import Catalog
from tests.test_recursive_r14 import manifest


class RecursiveR15Tests(unittest.TestCase):
    def test_protected_descendant_cannot_be_disabled_via_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = Runtime(tmp)
            names = {c['id'] for c in rt.visible_capabilities()}
            with self.assertRaisesRegex(ValueError, 'protected'):
                rt.execute('components.switch', {'unit':'mikoshi.ide', 'enabled':'false'})
            self.assertEqual(names, {c['id'] for c in rt.visible_capabilities()})
            self.assertNotIn('mikoshi.ide', rt.components.toggles)

    def test_invalid_persisted_toggle_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = Runtime(tmp)
            state = Path(tmp)/'components.json'
            state.write_text(json.dumps({'schema':'adamantium.switches.v1',
                                         'units':{'mikoshi.neural':'false'}}))
            with self.assertRaisesRegex(ValueError, 'Invalid saved unit toggle'):
                Runtime(tmp)
            state.write_text(json.dumps({'schema':'adamantium.switches.v1',
                                         'units':{'mikoshi.ide':False}}))
            with self.assertRaisesRegex(ValueError, 'protected'):
                Runtime(tmp)

    def test_atomic_reload_rejects_invalid_files_without_changing_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'units'
            manifest(root/'root', 'test.root', None, 'plugin')
            cat = Catalog(root, Path(tmp)/'state.json')
            manifest(root/'root'/'bad', 'test.bad', 'test.root', provides=[
                {'name':'test.cap', 'action':'invalid.action','prefix':'invalid.'}])
            with self.assertRaises(ValueError):
                cat.reload()
            self.assertEqual(set(cat.units), {'test.root'})
            (root/'root'/'bad'/'manifest.json').unlink()
            self.assertEqual(cat.reload()['units'],1)

    def test_reject_missing_and_non_boolean_contract_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'units'
            manifest(root/'root', 'test.root', None, 'plugin')
            for mutation in (
                {'enabled':'false'}, {'protected':1},
                {'requires':{'name':'a.b'}},
                {'requires':[{'name':'a.b','optional':'false'}]},
                {'requires':[{'name':'a.b','minimum':'one'}]},
                {'provides':[{'name':'a.b','prefix':3}]},
            ):
                path = root/'root'/'manifest.json'
                base=json.loads(path.read_text())
                path.write_text(json.dumps({**base, **mutation}))
                with self.subTest(mutation=mutation):
                    with self.assertRaises(ValueError):Catalog(root,Path(tmp)/'switches.json')
                path.write_text(json.dumps(base))

    def test_unclaimed_action_is_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = Runtime(tmp)
            rt.add('unregistered.action','Non-manifest action','unknown',[], lambda a:'no')
            self.assertNotIn('unregistered.action',
                             {c['id'] for c in rt.visible_capabilities()})
            with self.assertRaises(ValueError):rt.execute('unregistered.action',{})


if __name__=='__main__':unittest.main()
