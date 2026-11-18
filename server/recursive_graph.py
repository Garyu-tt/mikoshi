"""Readable live recursive graph; no synthetic provider or action nodes."""
from server import recursive_resolve as resolver


def build(catalog, live):
    enabled = catalog.enabled(live)
    actions = {c['id'] for c in live}
    nodes, edges = [], []
    for ident,unit in sorted(catalog.units.items()):
        own = [p for p in resolver.resolve(catalog.units,enabled, actions)
               if p['unit']==ident]
        nodes.append({'id':'unit:'+ident,'type':unit['kind'],'title':unit.get('title',ident),
                      'version':unit['version'],'enabled':catalog.enabled()[ident],
                      'ready':enabled[ident],
                      'isolation':unit.get('isolation','inprocess'),
                      'registered_providers':len(own),'path':unit['_path']})
        if unit.get('parent'):
            edges.append({'source':'unit:'+unit['parent'],'target':'unit:'+ident,
                          'relation':'contains'})
        for p in own:
            edges.append({'source':'unit:'+ident,'target':p['action'],
                          'relation':'provides_live'})
        for req in unit.get('requires', []):
            matched = catalog.provider(live,req)
            if matched:
                edges.append({'source':'unit:'+ident,'target':'unit:'+matched['unit'],
                              'relation':'uses_optional' if req.get('optional') else 'uses_required'})
    return {'schema':'adamantium.recursive-graph.v1','nodes':nodes,'edges':edges,
            'unclaimed_actions':sorted(a for a in actions if catalog.claim(a) is None)}
