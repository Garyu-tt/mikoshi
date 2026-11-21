"""CYCLON R0: trainable, shared-weight recurrent *toy* backend (not an 80B LLM)."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Agent:
    name: str
    hidden: np.ndarray
    a: np.ndarray
    b: np.ndarray
    feedback: int = 0
    steps: int = 0


class TwinCell:
    """One small shared core, two separately adapted recurrent states."""

    def __init__(self, width=48, rank=4, seed=23):
        if not (8 <= width <= 512 and 1 <= rank <= width):
            raise ValueError('invalid width/rank')
        rng = np.random.default_rng(seed)
        self.width = width
        self.embedding = rng.normal(0, .12, (256, width)).astype('f4')
        self.recurrent = (rng.normal(0, .3, (width, width)) /
                          np.sqrt(width)).astype('f4')
        self.peer = (rng.normal(0, .12, (width, width)) /
                     np.sqrt(width)).astype('f4')
        self.output = rng.normal(0, .08, (width, 256)).astype('f4')
        self.agents = {}
        for name in ('A', 'B'):
            a = rng.normal(0, .025, (width, rank)).astype('f4')
            b = np.zeros((rank, width), dtype='f4')
            self.agents[name] = Agent(name, np.zeros(width, 'f4'), a, b)

    @property
    def parameter_count(self):
        common = sum(x.size for x in (self.embedding, self.recurrent,
                                      self.peer, self.output))
        return common + sum(a.a.size + a.b.size for a in self.agents.values())

    def step(self, who, incoming=None, peer_hidden=None, target=None, lr=0.0):
        agent = self.agents[who]
        token = agent.feedback if incoming is None else int(incoming)
        if not 0 <= token < 256:
            raise ValueError('input byte out of range')
        other = (np.zeros(self.width, 'f4') if peer_hidden is None
                 else np.asarray(peer_hidden, dtype='f4'))
        if other.shape != (self.width,):
            raise ValueError('invalid peer state shape')
        before = agent.hidden.copy()
        z = (self.embedding[token] + before @ self.recurrent +
             other @ self.peer + (before @ agent.a) @ agent.b)
        new = np.tanh(z)
        logits = new @ self.output
        probs = np.exp(logits - np.max(logits))
        probs /= probs.sum()
        chosen = int(np.argmax(probs))
        loss = None
        if target is not None:
            if not 0 <= int(target) < 256:
                raise ValueError('target byte out of range')
            loss = -float(np.log(max(float(probs[int(target)]), 1e-12)))
            if lr:
                error = probs.copy()
                error[int(target)] -= 1
                grad_hidden = (self.output @ error) * (1 - new * new)
                grad_b = np.outer(before @ agent.a, grad_hidden)
                grad_a = np.outer(before, grad_hidden @ agent.b.T)
                self.output -= lr * np.outer(new, error)
                agent.a -= lr * grad_a
                agent.b -= lr * grad_b
        agent.hidden = new
        agent.feedback = chosen
        agent.steps += 1
        return {'token': chosen, 'loss': loss, 'step': agent.steps}

    def reset(self, who):
        self.agents[who].hidden.fill(0)
        self.agents[who].feedback = 0
        self.agents[who].steps = 0
