"""Live 2D neural telemetry; no animation-derived or invented spikes."""
from server.visual2d_validate import check


def project(engine):
    with engine.lock:
        fired = set(engine.spikes)
        nodes = [{**node, 'activity':1.0 if i in fired else 0.0,
                  'potential':engine.potential[i],
                  'refractory_ms':engine.refractory[i]}
                 for i,node in enumerate(engine.data['neurons'])]
        edges = [dict(e) for e in engine.data['synapses']]
        d = engine.data
        return check({'schema':'mikoshi.visual2d.v1',
            'id':'connectome.'+engine.id,'title':engine.id,
            'organ':d['organ'], 'projection':'topology' if d['organ']=='brain' else 'segmental',
            'coordinate_kind':d['coordinate_kind'],
            'source':{**d['source'],'kind':'live_neural_state',
                      'sha256':engine.source_sha256},
            'nodes':nodes,'edges':edges,'tick':engine.tick,
            'sample_at_ns':engine.at_ns, 'semantics':'measured_lif_spikes_this_tick',
            'layout_notice':'source_coordinates' if d['coordinate_kind']=='source' else 'derived_not_anatomical'})
