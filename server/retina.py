"""Opt-in adapter to the original R180 code, with source SHA pinning."""
import base64
import hashlib
import importlib.util
import threading
from pathlib import Path

EXPECTED_SHA = "67203cb15cdb94d3fa3976d789f3d7e2b0685ef8cf36c79527664294ac6d1e7a"


class RetinaR180:
    def __init__(self, path, width=920, height=920):
        path = Path(path).resolve()
        if path.name != "retina_r180.py" or not path.is_file():
            raise ValueError("Original retina_r180.py not found")
        if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED_SHA:
            raise ValueError("Source checksum mismatch: review required")
        if not (isinstance(width, int) and isinstance(height, int)):
            raise ValueError("Invalid retinal dimensions")
        spec = importlib.util.spec_from_file_location("mikoshi_legacy_retina_r180", path)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load original retina")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.mosaic = module.RetinalMosaic(width=width, height=height)
        self.width, self.height = width, height
        self.lock = threading.Lock()
        self.path = str(path)

    def status(self):
        return {"active": True, "implementation": "original-R180",
                "eyes": 2, "dimensions": [self.width, self.height],
                "source_sha256": EXPECTED_SHA,
                "frames": self.mosaic.frame_count,
                "no_depth_injection": True,
                "full_R257_stereo_ready": False}

    def step(self, args):
        if not isinstance(args, dict):
            raise ValueError("Arguments must be object")
        if not isinstance(args.get("frame_id"), int):
            raise ValueError("frame_id must be integer")
        size = self.width * self.height * 3
        frames = []
        for key in ("left_rgb_b64", "right_rgb_b64"):
            value = args.get(key)
            if not isinstance(value, str) or len(value) > (size * 4 // 3 + 8):
                raise ValueError("Frame size invalid")
            try:
                raw = base64.b64decode(value, validate=True)
            except Exception as exc:
                raise ValueError("Invalid RGB base64") from exc
            if len(raw) != size:
                raise ValueError("Expected post-optics RGB24 exact size")
            frames.append(raw)
        capture = args.get("sample_at_ns")
        domain = args.get("clock_domain")
        if not isinstance(capture, int) or capture <= 0:
            raise ValueError("Explicit positive sample_at_ns required")
        if domain not in ("unix-ns", "monotonic-ns"):
            raise ValueError("Explicit clock domain required")
        with self.lock:
            spikes, meta = self.mosaic.step(*frames, args["frame_id"],
                                             args.get("frame_ms", 33))
        # Small spikes are transportable. Large streams require optic bus integration.
        return {"metadata": meta, "sample_at_ns": capture, "clock_domain": domain,
                "spikes_sha256": hashlib.sha256(spikes).hexdigest(),
                "spikes_b64": base64.b64encode(spikes).decode() if len(spikes) < 150000 else None,
                "stream_truncated": len(spikes) >= 150000}
