"""Independent recursive unit state and graph. No optional peer is assumed."""
import json
import os
import threading
import uuid
from pathlib import Path
from server import recursive_load, recursive_resolve as resolver


class Catalog:
    def __init__(self, manifests, state_file):
        self.manifests = Path(manifests)
        self.state_file = Path(state_file)
        self.lock = threading.RLock()
        self.units = recursive_load.discover(self.manifests)
        self.toggles = {}
        if self.state_file.is_file():
            obj = json.loads(self.state_file.read_text(encoding='utf-8'))
            if obj.get('schema') != 'adamantium.switches.v1':
                raise ValueError('Unknown unit toggle state')
            self.toggles = obj['units']

    def enabled(self, live=None):
        configured = resolver.eligible(self.units, self.toggles)
        if live is None:
            return configured
        actions = {c['id'] for c in live}
        ready = {key:False for key in self.units}
        for _ in self.units:
            progressed = False
            for key, unit in self.units.items():
                parent = unit.get('parent')
                if ready[key] or not configured[key] or (parent and not ready[parent]):
                    continue
                if any(not req.get('optional', False) and not
                       resolver.resolve(self.units, ready, actions, req)
                       for req in unit.get('requires', [])):
                    continue
                ready[key] = progressed = True
            if not progressed:
                break
        return ready

    def claim(self, action):
        return resolver.owner(self.units, action)

    def actions(self, live):
        enabled = self.enabled(live)
        return [c for c in live if not (self.claim(c['id']) and
                not enabled[self.claim(c['id'])])]

    def provider(self, live, request):
        actions = {c['id'] for c in self.actions(live)}
        ready = self.enabled(live)
        return resolver.resolve(self.units, ready, actions, request)

    def switch(self, ident, enabled):
        if ident not in self.units or type(enabled) is not bool:
            raise ValueError('Unknown unit or invalid toggle')
        if self.units[ident].get('protected'):
            raise ValueError('Protected unit must remain accessible')
        with self.lock:
            latest = dict(self.toggles)
            latest[ident] = enabled
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            candidate = self.state_file.with_name('.'+uuid.uuid4().hex+'.new')
            fd = os.open(candidate, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as handle:
                    json.dump({'schema':'adamantium.switches.v1','units':latest},handle)
                    handle.flush(); os.fsync(handle.fileno())
                os.replace(candidate,self.state_file)
            finally:
                candidate.unlink(missing_ok=True)
            self.toggles = latest
            return {'id':ident,'enabled':self.enabled()[ident]}

    def reload(self):
        with self.lock:
            latest = recursive_load.discover(self.manifests)
            self.units = latest
            return {'units':len(latest),'source':'local_verified_manifests',
                    'code_hotloaded':False}

    def graph(self, live):
        enabled = self.enabled(live)
        actions = {c['id'] for c in live}
        nodes, edges = [], []
        for ident,unit in sorted(self.units.items()):
            own = [p for p in resolver.resolve(self.units,enabled, actions)
                   if p['unit']==ident]
            nodes.append({'id':'unit:'+ident,'type':unit['kind'],'title':unit.get('title',ident),
                          'version':unit['version'],'enabled':self.enabled()[ident],
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
                matched = self.provider(live,req)
                if matched:
                    edges.append({'source':'unit:'+ident,'target':'unit:'+matched['unit'],
                                  'relation':'uses_optional' if req.get('optional') else 'uses_required'})
        return {'schema':'adamantium.recursive-graph.v1','nodes':nodes,'edges':edges,
                'unclaimed_actions':sorted(a for a in actions if self.claim(a) is None)}
