"""Every graph fixture here is labeled test data, never a connectome claim."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server.visual2d_index_import import build
from server.visual2d_index_read import info, window
from server.runtime import Runtime
from server.graph_union import build as unified


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.meta = self.base/'meta.json'
        self.nodes = self.base/'nodes.jsonl'
        self.edges = self.base/'edges.jsonl'
        self.db = self.base/'neurons.m2d.sqlite'
        self.meta.write_text(json.dumps({'schema':'mikoshi.visual2d.v1',
            'id':'brain.unit','title':'Unit test only','organ':'brain',
            'projection':'topology','coordinate_kind':'source',
            'source':{'id':'test:unit-data'}}))
        self.nodes.write_text('\n'.join(json.dumps(n) for n in [
            {'id':'n.0','x':.25,'y':.25,'activity':.2},
            {'id':'n.1','x':.75,'y':.75,'activity':.9},
            {'id':'n.2','x':.30,'y':.30,'activity':0}])+'\n')
        self.edges.write_text(json.dumps({'source':'n.0','target':'n.2'})+'\n')

    def test_index_viewport_and_live_capabilities(self):
        result=build(self.meta,self.nodes,self.edges,self.db)
        self.assertEqual(result['nodes_total'],3)
        self.assertEqual(len(result['nodes_sha256']),64)
        self.assertEqual(info(self.db)['id'],'brain.unit')
        view=window(self.db,(0,0,.5,.5),10)
        self.assertEqual({n['id'] for n in view['nodes']},{'n.0','n.2'})
        self.assertEqual(len(view['edges']),1)
        self.assertFalse(view['window']['partial'])
        self.assertEqual({n['id'] for n in window(self.db,limit=1)['nodes']},{'n.0'})
        self.assertTrue(window(self.db,limit=1)['window']['partial'])
        with patch.dict(os.environ,{'MIKOSHI_VISUAL2D_DIR':str(self.base)}):
            app=Runtime(self.base/'state')
            self.assertIn('visual2d.open.brain.unit',app.handlers)
            self.assertIn('visual2d.query.brain.unit',app.handlers)
            result=app.execute('visual2d.query.brain.unit',
                {'x0':0,'y0':0,'x1':.5,'y1':.5,'limit':10})
            self.assertEqual(len(result['nodes']),2)
            graph=unified(app)
            self.assertIn('view2d:brain.unit',{n['id'] for n in graph['nodes']})
            self.db.unlink();app.update_views()
            self.assertNotIn('visual2d.query.brain.unit',app.handlers)

    def test_failure_never_creates_partial_index(self):
        self.edges.write_text(json.dumps({'source':'n.0','target':'missing'})+'\n')
        with self.assertRaises(Exception):build(self.meta,self.nodes,self.edges,self.db)
        self.assertFalse(self.db.exists())
        self.assertFalse(list(self.base.glob('.*.m2d.sqlite')))

    def test_validation_and_nonoverwrite(self):
        build(self.meta,self.nodes,self.edges,self.db)
        with self.assertRaises(ValueError):build(self.meta,self.nodes,self.edges,self.db)
        for b in ((0,0,2,1),(1,0,0,1),(0,0,float('nan'),1)):
            with self.assertRaises(ValueError):window(self.db,b)
        with self.assertRaises(ValueError):window(self.db,limit=99999)
        self.assertEqual(len(window(self.db,(.7,.7,1,1))['nodes']),1)

    def test_spinal_require_real_segment(self):
        meta=json.loads(self.meta.read_text());meta['organ']='spinal'
        meta['projection']='segmental'
        self.meta.write_text(json.dumps(meta))
        with self.assertRaises(ValueError):build(self.meta,self.nodes,self.edges,self.db)
