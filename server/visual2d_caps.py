"""Only discover actions backed by live sensors or validated data."""
import os
from server.visual2d_registry import Registry
from server.visual2d_retina import project
from server.visual2d_axons import project as project_axons
from server.connectome_view import project as project_connectome

PREFIX = 'visual2d.open.'
QUERY = 'visual2d.query.'


def list_available(runtime):
    rows = runtime.visual2d.available()
    seen = {r['id'] for r in rows}
    for key, engine in runtime.connectomes.items():
        ident = 'connectome.' + key
        if ident not in seen:
            rows.append({'id':ident, 'organ':engine.data['organ'],
                         'title':'Neural: '+key, 'source':engine.data['source'],
                         'state':'live_neural_state'})
            seen.add(ident)
    if runtime.sparse is not None:
        for eye in ('left','right'):
            id_ = 'retina.' + eye
            if id_ not in seen:
                rows.append({'id':id_, 'organ':'retina',
                             'title':'Реальная сетчатка: '+eye,
                             'source':{'id':'retina.r239'},'state':'live_sensor'})
        for side in ('left','right'):
            ident = 'retina.axons.'+side
            if ident not in seen:
                rows.append({'id':ident, 'organ':'retina',
                             'title':'Активность зрительных аксонов: '+side,
                             'source':{'id':'retina.r239'},'state':'live_axons'})
    return rows


def sync(runtime):
    rows = list_available(runtime)
    needed = {PREFIX+r['id']:r for r in rows}
    queries = {QUERY+r['id']:r for r in rows if r['state']=='indexed_read_only'}
    allowed = {**needed,**queries}
    for name in list(runtime.handlers):
        if name.startswith((PREFIX,QUERY)) and name not in allowed:
            del runtime.handlers[name]
    runtime.capabilities[:] = [c for c in runtime.capabilities if
        not c['id'].startswith((PREFIX,QUERY)) or c['id'] in allowed]
    for name,row in needed.items():
        if name in runtime.handlers:
            continue
        if row['state']=='live_neural_state':
            runtime.add(name,'2D: '+row['title'],'mikoshi.visual2d',[],
                        lambda a,key=row['id'][len('connectome.'):]:
                        project_connectome(runtime.connectomes[key]))
        elif row['state']=='live_axons':
            runtime.add(name,'2D: '+row['title'],'mikoshi.visual2d',[],
                        lambda a,side=row['id'].split('.')[-1]:
                        project_axons(runtime.sparse,runtime.spike_store,side))
        elif row['state']=='live_sensor':
            runtime.add(name,'2D: '+row['title'],'mikoshi.visual2d',[],
                        lambda a,side=row['id'].split('.')[1]: project(runtime.sparse,side))
        else:
            runtime.add(name,'2D: '+row['title'],'mikoshi.visual2d',[],
                        lambda a,view_id=row['id']: runtime.visual2d.open(view_id))
    fields=[{'name':k,'type':'fraction','optional':True} for k in
            ('x0','y0','x1','y1')]
    fields.append({'name':'limit','type':'number','optional':True})
    for name,row in queries.items():
        if name not in runtime.handlers:
            runtime.add(name,'Область 2D: '+row['title'],'mikoshi.visual2d',fields,
                        lambda a,view_id=row['id']:runtime.visual2d.query(view_id,a))
    runtime.visual2d_views = rows


def install(runtime):
    runtime.visual2d = Registry(os.getenv('MIKOSHI_VISUAL2D_DIR'))
    runtime.visual2d_views = []
    runtime.add('visual2d.list','Доступные 2D-карты','mikoshi.visual2d',[],
                lambda a:{'views':list_available(runtime),'no_synthetic_connectomes':True})
    sync(runtime)
