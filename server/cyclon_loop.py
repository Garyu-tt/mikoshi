"""Bounded, synchronous twin dialogue; supports autonomous recurrent steps."""
from collections import deque
from server.cyclon_core import TwinCell


class TwinLoop:
    def __init__(self, model=None, depth=2, history=64):
        if not 1 <= depth <= 8 or not 1 <= history <= 1024:
            raise ValueError('invalid compute budget')
        self.model = model or TwinCell()
        self.depth = depth
        self.events = deque(maxlen=history)
        self.inputs = {'A': deque(), 'B': deque()}
        self.ticks = 0

    def submit(self, who, text):
        if who not in self.inputs:
            raise ValueError('unknown twin')
        data = text.encode('utf-8')
        if len(data) > 4096 or len(self.inputs[who]) + len(data) > 4096:
            raise ValueError('input budget exceeded')
        self.inputs[who].extend(data)

    def tick(self):
        """Both agents see peers' previous state, not each other's future."""
        report = {}
        for _ in range(self.depth):
            snapshot = {k: a.hidden.copy() for k, a in self.model.agents.items()}
            for who, peer in (('A', 'B'), ('B', 'A')):
                incoming = self.inputs[who].popleft() if self.inputs[who] else None
                report[who] = self.model.step(who, incoming, snapshot[peer])
        self.ticks += 1
        event = {'tick': self.ticks, 'A': report['A']['token'],
                 'B': report['B']['token'], 'depth': self.depth}
        self.events.append(event)
        return event

    def run(self, ticks=1):
        if not 1 <= ticks <= 1024:
            raise ValueError('bounded run only')
        return [self.tick() for _ in range(ticks)]

    def diagnostics(self):
        return {'ticks': self.ticks, 'shared_parameter_count':
                self.model.parameter_count,
                'agents': {k: {'steps': a.steps, 'queued_bytes': len(self.inputs[k])}
                           for k, a in self.model.agents.items()},
                'last_events': list(self.events)[-8:]}

    def train_text(self, who, text, lr=.01, max_bytes=4096):
        """Online one-step next-byte learning, not full recurrent BPTT."""
        data = text.encode('utf-8')[:max_bytes]
        if len(data) < 2:
            return None
        losses = []
        for a, b in zip(data, data[1:]):
            losses.append(self.model.step(who, a, target=b, lr=lr)['loss'])
        return sum(losses) / len(losses)
