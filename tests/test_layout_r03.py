import tempfile
import unittest
from server.runtime import Runtime


class GraphLayoutR03Tests(unittest.TestCase):
    def test_each_button_is_an_independent_graph_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = Runtime(tmp)
            left = rt.execute('layout.create_tab', {'title':'Визуальная кора'})
            right = rt.execute('layout.create_tab', {'title':'Фовеа','parent':left['id']})
            a = rt.execute('layout.place', {'action':'retina.status','tab':left['id'],
                                             'area':'toolbar'})
            b = rt.execute('layout.place', {'action':'retina.status','tab':left['id'],
                                             'area':'footer'})
            self.assertNotEqual(a['id'], b['id'])
            rt.execute('layout.move', {'placement':b['id'],'tab':right['id'],
                                        'area':'sidebar','row':1,'column':2})
            g = rt.layout.graph(rt.capabilities)
            self.assertTrue(any(n['id']==b['id'] and n['type']=='button'
                                and n['area']=='sidebar' for n in g['nodes']))
            self.assertTrue(any(e['source']==left['id'] and e['target']==right['id']
                                for e in g['edges']))
            self.assertTrue(any(n['type']=='module' for n in g['nodes']))
            self.assertEqual(len(g['placements']),2)
            rt.execute('layout.remove', {'placement':a['id']})
            with self.assertRaises(ValueError):
                rt.execute('layout.tab_delete', {'tab':right['id']})
            rt.execute('layout.remove', {'placement':b['id']})
            rt.execute('layout.tab_delete', {'tab':right['id']})
            self.assertEqual(len(rt.layout.graph(rt.capabilities)['placements']),0)

    def test_tab_cycle_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt=Runtime(tmp)
            a=rt.execute('layout.create_tab', {'title':'A'})
            b=rt.execute('layout.create_tab', {'title':'B','parent':a['id']})
            with self.assertRaises(ValueError):
                rt.execute('layout.tab_edit', {'tab':a['id'],'parent':b['id']})

    def test_nanoseconds_preserved_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt=Runtime(tmp)
            raw='1794960000123456789'
            rt.execute('nervous.publish', {'source':'camera','topic':'photon',
                'source_sequence':'0','at_ns':raw,'clock_domain':'unix-ns',
                'payload':{'kind':'real-sample'}})
            events=rt.execute('nervous.read', {})['items']
            self.assertEqual(events[0]['sample_at_ns'], int(raw))
            with self.assertRaises(ValueError):
                rt.execute('nervous.publish', {'source':'camera','topic':'photon',
                    'source_sequence':'1.2','at_ns':raw,
                    'clock_domain':'unix-ns','payload':{}})
