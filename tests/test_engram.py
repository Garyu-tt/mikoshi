import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from server import engram


class EngramTests(unittest.TestCase):
    def test_research_engrams_are_not_brains(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "retina.engram"
            engram.create(p, {"research/gate.json": b'{"promotion":"BLOCKED"}'})
            x = engram.verify(p)
            self.assertEqual(x["kind"], "research")
            self.assertFalse(x["state_present"])

    def test_neural_state_required(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                engram.create(Path(temp) / "dante.engram", {"note": b"x"}, "specimen")

    def test_corrupt_blob_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "bad.engram"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("manifest.json", json.dumps({"format":"mikoshi-engram.v1",
                            "kind":"research","blobs":[{"name":"blob","bytes":2,"sha256":"f"*64}]}))
                z.writestr("blob", b"ok")
            with self.assertRaises(ValueError):
                engram.verify(p)
