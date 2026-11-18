"""Bounded CPU LIF dynamics over an owner-provided sparse neural topology."""
import hashlib
import math
import threading
from server.connectome_validate import check, finite


class Connectome:
    def __init__(self, topology, source_bytes):
        self.data = check(topology)
        self.source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        self.id = topology['id']
        self.lock = threading.RLock()
        self.names = [n['id'] for n in topology['neurons']]
        self.by_id = {name: i for i, name in enumerate(self.names)}
        self.out = [[] for _ in self.names]
        for e in topology['synapses']:
            self.out[self.by_id[e['source']]].append((self.by_id[e['target']], float(e['weight'])))
        self.potential = [0.] * len(self.names)
        self.refractory = [0.] * len(self.names)
        self.spikes = []
        self.tick = 0
        self.at_ns = 0
        self.clock_domain = None
        self.source_bytes = source_bytes
        self.source_detached = False

    def step(self, args):
        when = args.get('sample_at_ns')
        domain = args.get('clock_domain')
        pulse = args.get('pulses', {})
        if type(when) is not int or when <= 0 or domain not in ('unix-ns', 'monotonic-ns'):
            raise ValueError('Explicit valid sensor timestamp/clock required')
        if not isinstance(pulse, dict) or len(pulse) > len(self.names):
            raise ValueError('Invalid neural stimulus')
        if any(k not in self.by_id or not finite(v, -10, 10) for k, v in pulse.items()):
            raise ValueError('Unknown neuron or non-finite stimulation')
        with self.lock:
            if self.source_detached:
                raise ValueError("Source changed/removed: snapshot state, restore pinned source")
            if when <= self.at_ns or (self.clock_domain and self.clock_domain != domain):
                raise ValueError('Nonmonotonic or incompatible neural clock')
            drive = [0.] * len(self.names)
            for i in self.spikes:
                for j, weight in self.out[i]:
                    drive[j] += weight
            dt = float(self.data['dt_ms'])
            fired = []
            for i, n in enumerate(self.data['neurons']):
                if self.refractory[i] > 0:
                    self.refractory[i] = max(0., self.refractory[i] - dt)
                    self.potential[i] = 0.
                    continue
                decay = math.exp(-dt / n['tau_ms'])
                value = self.potential[i] * decay + drive[i] + pulse.get(n['id'], 0.)
                if value >= n['threshold']:
                    fired.append(i)
                    value = 0.
                    self.refractory[i] = float(n.get('refractory_ms', 0.))
                self.potential[i] = max(-1000., min(1000., value))
            self.spikes = fired
            self.at_ns, self.clock_domain = when, domain
            self.tick += 1
            return {'source_id':self.id, 'tick':self.tick,
                    'source_sequence':self.tick, 'spike_ids':[self.names[i] for i in fired],
                    'sample_at_ns':when, 'clock_domain':domain,
                    'dynamics':'cpu_lif_discrete_dt', 'motor_enabled':False}

    def status(self):
        with self.lock:
            return {'id':self.id,'organ':self.data['organ'], 'loaded':True,
                    'execution_mode':'request_driven_not_continuous',
                    'engine':'cpu-lif-v1','neurons':len(self.names),
                    'synapses':len(self.data['synapses']), 'tick':self.tick,
                    'source_sha256':self.source_sha256,
                    'source_provenance':self.data['source'], 'motor_enabled':False,
                    'source_detached':self.source_detached}
