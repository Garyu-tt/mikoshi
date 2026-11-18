"""Synthetic test only, not a real connectome."""
import json
from server import engram
from server.graph_union import build
from connectome_fixture_r06 import ConnectomeFixture, dataset


class ConnectomeTests(ConnectomeFixture):
    def test_dynamic_execution_and_true_spikes_in_2d(self):
        rt=self.runtime()
        self.assertFalse(any('connectome.step.' in x for x in rt.handlers))
        self.write();rt.update_views()
        self.assertIn('connectome.step.labtest',rt.handlers)
        first=self.step(rt,1000,{'n0':1.25})
        self.assertEqual(first['spike_ids'],['n0'])
        second=self.step(rt,2000)
        self.assertEqual(second['spike_ids'],['n1'])
        view=rt.execute('visual2d.open.connectome.labtest',{})
        self.assertEqual([n['activity'] for n in view['nodes']],[0,1])
        self.assertEqual(view['source']['kind'],'live_neural_state')
        self.assertEqual(rt.execute('nervous.read',{})['items'][-1]['payload']['count'],1)
        self.assertIn('view2d:connectome.labtest',{n['id'] for n in build(rt)['nodes']})
        with self.assertRaises(ValueError):self.step(rt,2000)

    def test_neural_specimen_roundtrip_deterministic(self):
        self.write();rt=self.runtime()
        self.step(rt,1000,{'n0':1.25});self.step(rt,2000)
        snap=rt.execute('engram.snapshot.labtest',{'name':'test-state'})
        self.assertTrue(snap['state_present']);self.assertEqual(snap['kind'],'specimen')
        a=self.step(rt,3000,{'n1':.25})
        again=self.runtime('new-state')
        again.vault=rt.vault
        self.assertEqual(again.execute('engram.restore.labtest',
            {'filename':'test-state.engram'})['tick'],2)
        b=self.step(again,3000,{'n1':.25})
        self.assertEqual(a['spike_ids'],b['spike_ids'])
        self.assertEqual(rt.connectomes['labtest'].potential,
                         again.connectomes['labtest'].potential)
        with self.assertRaisesRegex(ValueError,'overwrite running'):
            again.execute('engram.restore.labtest',{'filename':'test-state.engram'})
        with self.assertRaises(Exception):
            rt.execute('engram.snapshot.labtest',{'name':'test-state'})

    def test_modified_source_keeps_state_but_blocks_stepping(self):
        self.write();rt=self.runtime();self.step(rt,1000,{'n0':2})
        raw=self.name.read_text();model=dataset();model['synapses'][0]['weight']=2
        self.name.write_text(json.dumps(model));rt.update_views()
        status=rt.execute('connectome.status.labtest',{})
        self.assertTrue(status['source_detached'])
        with self.assertRaisesRegex(ValueError,'Source changed'):
            self.step(rt,2000)
        self.assertEqual(rt.execute('engram.snapshot.labtest',{'name':'salvage'})['kind'],'specimen')
        self.name.write_text(raw);rt.update_views()
        self.assertFalse(rt.execute('connectome.status.labtest',{})['source_detached'])
        self.assertEqual(self.step(rt,2000)['tick'],2)
        self.name.unlink();rt.update_views()
        self.assertTrue(rt.execute('connectome.status.labtest',{})['source_detached'])

    def test_rejects_fake_neurons_and_wrong_topology(self):
        m=dataset();m['synapses'][0]['target']='ghost';self.write(m)
        rt=self.runtime();self.assertNotIn('connectome.step.labtest',rt.handlers)
        m=dataset();m['neurons'][0]['threshold']=float('nan');self.write(m)
        rt.update_views();self.assertNotIn('connectome.step.labtest',rt.handlers)
        self.write();rt.update_views();self.step(rt,1000,{'n0':2})
        rt.execute('engram.snapshot.labtest',{'name':'valid'})
        other=self.runtime('other');other.vault=rt.vault
        new=dataset();new['synapses'][0]['weight']=1.9;self.write(new)
        other.update_views()
        with self.assertRaisesRegex(ValueError,'mismatch|differ'):
            other.execute('engram.restore.labtest',{'filename':'valid.engram'})
        self.assertFalse(other.connectomes['labtest'].tick)

    def test_spinal_segment_and_untrusted_action_bounds(self):
        self.write(dataset('spinal'));rt=self.runtime()
        view=rt.execute('visual2d.open.connectome.labtest',{})
        self.assertEqual(view['organ'],'spinal')
        self.assertEqual(view['projection'],'segmental')
        for pulses in ({'ghost':1},{'n0':float('nan')},{'n0':100}):
            with self.assertRaises(ValueError):self.step(rt,1000,pulses)
        self.assertEqual(rt.connectomes['labtest'].tick,0)

    def test_research_archive_cannot_restore_and_specimen_cannot_forge(self):
        self.write();rt=self.runtime()
        research=rt.execute('engram.snapshot_research',{'name':'notes'})
        self.assertFalse(research['state_present'])
        with self.assertRaisesRegex(ValueError,'research'):
            rt.execute('engram.restore.labtest',{'filename':'notes.engram'})
        with self.assertRaises(ValueError):
            engram.create(rt.vault/'false.engram',{'neural/not-state.txt':b'hi'},'specimen')
