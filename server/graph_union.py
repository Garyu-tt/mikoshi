"""Live unified view: executable UI, source provenance, architecture, heritage."""
import inspect
from pathlib import Path
from server import codemap, heritage, module_graph, motor_registry

ROOT = Path(__file__).resolve().parent.parent


def build(runtime):
    layout = runtime.layout.graph(runtime.visible_capabilities())
    source = codemap.graph()
    modules = module_graph.build()
    historical = heritage.research_graph()
    nodes = list(layout['nodes']) + source['nodes']
    edges = list(layout['edges']) + source['edges']
    used = {n['id'] for n in nodes}
    for c in runtime.visible_capabilities():
        fn = runtime.handlers.get(c['id'])
        try:
            file = Path(inspect.getsourcefile(fn)).resolve().relative_to(ROOT).as_posix()
        except (TypeError, ValueError, AttributeError):
            continue
        target = 'file:' + file
        if target in used:
            edges.append({'source': c['id'], 'target': target,
                          'relation': 'implemented_in'})
    for view in getattr(runtime, 'visual2d_views', []):
        vid = 'view2d:' + view['id']
        nodes.append({'id':vid, 'type':'visualization',
                      'organ':view['organ'], 'title':view['title'],
                      'source':view['source'], 'state':view['state']})
        edges.append({'source':'visual2d.open.'+view['id'],
                      'target':vid, 'relation':'renders'})
        if view['state']=='indexed_read_only':
            edges.append({'source':'visual2d.query.'+view['id'],
                          'target':vid, 'relation':'queries_viewport'})
    for n in modules['nodes']:
        new = dict(n);new['id'] = 'arch:' + n['id'];new['type'] = 'architecture'
        new['provenance'] = 'declared_not_necessarily_running'
        nodes.append(new)
    for e in modules['edges']:
        edges.append({'source':'arch:'+e['source'], 'target':'arch:'+e['target'],
                      'relation':e['relation']})
    source_ids = {item['id'] for item in source['nodes']}
    recursive = runtime.components.graph(runtime.visible_capabilities())
    nodes.extend(recursive['nodes'])
    edges.extend(recursive['edges'])
    for n in recursive['nodes']:
        file_ref = 'file:units/' + n['path'] + '/manifest.json'
        if file_ref in source_ids:
            edges.append({'source':n['id'],'target':file_ref,'relation':'declared_in'})
    for n in historical['nodes']:
        new = dict(n);new['id'] = 'history:' + n['id']
        new['provenance'] = 'historical_reported_not_live'
        nodes.append(new)
    for e in historical['edges']:
        edges.append({'source':'history:'+e['source'], 'target':'history:'+e['target'],
                      'relation':e.get('relation','historical')})
    for record in motor_registry.discover():
        origin = 'arch:mikoshi.motor.' + record['id']
        file = 'file:heritage/motor_calibrations/' + record['id'] + '.json'
        action = 'motor.calibration.' + record['id'] + '.read'
        edges.append({'source':origin,'target':file,
                      'relation':'original_calibration_evidence'})
        if action in runtime.handlers:
            edges.append({'source':action,'target':origin,
                          'relation':'reads_cited_motor_report'})
        derived = 'motor.calibration.' + record['id'] + '.response'
        if derived in runtime.handlers:
            edges.append({'source':derived,'target':origin,
                          'relation':'analyzes_observed_motor_response_only'})
    allids = {n['id'] for n in nodes}
    if len(allids) != len(nodes):
        raise ValueError('Duplicate unified graph node')
    if any(e['source'] not in allids or e['target'] not in allids for e in edges):
        raise ValueError('Dangling unified graph edge')
    return {'schema':'mikoshi.unified-graph.v1','nodes':nodes,'edges':edges,
            'live':sum(n.get('type') in ('action','button','tab') for n in nodes),
            'heritage_nodes':len(historical['nodes']),
            'source_files':source['total']}
