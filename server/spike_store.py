"""Bounded, exact raw optic-spike packet retrieval for active IDE clients."""
import base64
import hashlib
import threading
from collections import OrderedDict


class SpikeStore:
    def __init__(self, max_packets=8, max_bytes=64 * 1024 * 1024):
        self.lock = threading.RLock()
        self.packets = OrderedDict()
        self.max_packets, self.max_bytes = max_packets, max_bytes
        self.used = 0

    def put(self, sequence, raw):
        if type(sequence) is not int or sequence < 0 or not isinstance(raw, bytes):
            raise ValueError('Invalid spike packet')
        if len(raw) % 8:
            raise ValueError('R239 spike packet is not composed of 8-byte events')
        sha = hashlib.sha256(raw).hexdigest()
        with self.lock:
            if sequence in self.packets:
                raise ValueError('Duplicate optic sequence')
            retained = len(raw) <= self.max_bytes
            if retained:
                while self.packets and (self.used + len(raw) > self.max_bytes or
                                        len(self.packets) >= self.max_packets):
                    _, old = self.packets.popitem(last=False)
                    self.used -= len(old)
                self.packets[sequence] = raw
                self.used += len(raw)
        return {'sequence': sequence, 'bytes': len(raw), 'sha256': sha,
                'retained': retained, 'read_action': 'retina.r239.spikes.read'
                if retained else None}

    def latest(self):
        with self.lock:
            if not self.packets:
                return None
            seq = next(reversed(self.packets))
            return seq, self.packets[seq]

    def clear(self):
        with self.lock:
            self.packets.clear()
            self.used = 0

    def read(self, args):
        seq, offset, limit = (args.get('sequence'), args.get('offset', 0),
                              args.get('limit', 8192))
        if (type(seq) is not int or seq < 0 or type(offset) is not int or
                offset < 0 or type(limit) is not int or not 1 <= limit <= 32768):
            raise ValueError('Invalid optic retrieval cursor/limit')
        with self.lock:
            if seq not in self.packets:
                raise ValueError('Optic packet expired or was never retained')
            raw = self.packets[seq]
            if offset > len(raw):
                raise ValueError('Optic cursor out of bounds')
            piece = raw[offset:offset + limit]
            return {'sequence': seq, 'offset': offset, 'next_offset': offset + len(piece),
                    'bytes': len(raw), 'done': offset + len(piece) == len(raw),
                    'sha256': hashlib.sha256(raw).hexdigest(),
                    'raw_b64': base64.b64encode(piece).decode('ascii')}
