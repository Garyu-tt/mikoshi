"""Independent recursive unit state and graph. No optional peer is assumed."""
import json
import os
import threading
import uuid
from pathlib import Path
from server import recursive_load, recursive_resolve as resolver
from server.recursive_manifest import ident as valid_id


class Catalog:
    def __init__(self, manifests, state_file):
        self.manifests = Path(manifests)
        self.state_file = Path(state_file)
        self.lock = threading.RLock()
        self.units = recursive_load.discover(self.manifests)
        self.toggles = {}
        if self.state_file.is_file():
            obj = json.loads(self.state_file.read_text(encoding='utf-8'))
            if obj.get('schema') != 'adamantium.switches.v1' or not isinstance(obj.get('units'), dict):
                raise ValueError('Unknown unit toggle state')
            if any(not valid_id(k) or type(v) is not bool for k,v in obj['units'].items()):
                raise ValueError('Invalid saved unit toggle')
            self.toggles = obj['units']
        self._protected_ready(self.units, self.toggles)

    def _protected_under(self, ancestor):
        for ident, unit in self.units.items():
            if not unit.get('protected'):
                continue
            current = ident
            while current:
                if current == ancestor:
                    return True
                current = self.units[current].get('parent')
        return False

    @staticmethod
    def _protected_ready(units, toggles):
        ready = resolver.eligible(units, toggles)
        if any(unit.get('protected') and not ready[key]
               for key, unit in units.items()):
            raise ValueError('Configured state would disable a protected unit')

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
        return [c for c in live if self.claim(c['id']) is not None and
                enabled[self.claim(c['id'])]]

    def provider(self, live, request):
        actions = {c['id'] for c in self.actions(live)}
        ready = self.enabled(live)
        return resolver.resolve(self.units, ready, actions, request)

    def switch(self, ident, enabled):
        if ident not in self.units or type(enabled) is not bool:
            raise ValueError('Unknown unit or invalid toggle')
        if not enabled and self._protected_under(ident):
            raise ValueError('Cannot disable protected unit or ancestor')
        with self.lock:
            latest = dict(self.toggles)
            latest[ident] = enabled
            self._protected_ready(self.units, latest)
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
            self._protected_ready(latest, self.toggles)
            self.units = latest
            return {'units':len(latest),'source':'local_verified_manifests',
                    'code_hotloaded':False}

    def graph(self, live):
        from server.recursive_graph import build
        return build(self, live)
