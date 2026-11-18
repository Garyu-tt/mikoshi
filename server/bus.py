"""Actual bounded, ordered neural event transport; not a connectome solver."""
import json
import re
import threading
import time
from collections import deque

ID = re.compile(r"^[a-zA-Z0-9_.-]{1,96}$")


class NeuralBus:
    def __init__(self, max_events=2048):
        self.events = deque(maxlen=max_events)
        self.lock = threading.RLock()
        self.sequence = {}
        self.offset = 0

    def publish(self, source, topic, source_sequence, at_ns, payload, clock_domain):
        if not (isinstance(source, str) and ID.fullmatch(source)
                and isinstance(topic, str) and ID.fullmatch(topic)):
            raise ValueError("Invalid neural bus source/topic")
        if not isinstance(source_sequence, int) or source_sequence < 0:
            raise ValueError("Invalid source sequence")
        if not isinstance(at_ns, int) or at_ns <= 0:
            raise ValueError("Invalid observation timestamp")
        if clock_domain not in ("unix-ns", "monotonic-ns"):
            raise ValueError("Explicit clock_domain required")
        if not isinstance(payload, dict):
            raise ValueError("Payload must be an object")
        if len(json.dumps(payload, allow_nan=False).encode()) > 16384:
            raise ValueError("Neural event too large")
        with self.lock:
            key = (source, topic)
            if source_sequence <= self.sequence.get(key, -1):
                raise ValueError("Stale or duplicated source event")
            self.offset += 1
            event = {"event_id": self.offset, "source": source, "topic": topic,
                     "source_sequence": source_sequence, "sample_at_ns": at_ns,
                     "clock_domain": clock_domain,
                     "recorded_at_ns": time.time_ns(), "payload": payload}
            self.events.append(event)
            self.sequence[key] = source_sequence
            return {"accepted": True, "event_id": self.offset}

    def read(self, after=0, limit=100):
        if not isinstance(after, int) or after < 0:
            raise ValueError("Invalid event cursor")
        if not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("Invalid event limit")
        with self.lock:
            oldest = self.events[0]["event_id"] if self.events else self.offset + 1
            return {"items": [dict(e) for e in self.events if e["event_id"] > after][:limit],
                    "oldest_id": oldest, "newest_id": self.offset,
                    "overrun": after != 0 and after < oldest - 1,
                    "kind": "bounded_transport_not_connectome"}

    def stats(self):
        with self.lock:
            return {"newest_id": self.offset, "retained": len(self.events),
                    "sources": len(self.sequence), "subscriber_count": 0,
                    "persistence": "none", "physical_motor_link": False}
