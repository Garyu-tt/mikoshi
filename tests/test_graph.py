import tempfile
import unittest
from pathlib import Path
from server.layout import Layout
from server.runtime import Runtime
from server import heritage


class GraphTests(unittest.TestCase):
    def test_tabs_placements_persist(self):
        with tempfile.TemporaryDirectory() as temp:
            layout = Layout(Path(temp) / "menu.json")
            tab = layout.tab("Сетчатка")
            e = layout.place("retina.status", tab["id"], {"retina.status": True})
            self.assertEqual(e["source"], "retina.status")
            self.assertEqual(len(Layout(Path(temp) / "menu.json").state["placements"]), 1)

    def test_never_place_unknown_action(self):
        with tempfile.TemporaryDirectory() as temp:
            layout = Layout(Path(temp) / "menu.json")
            tab = layout.tab("Test")
            with self.assertRaises(ValueError):
                layout.place("retina.r257.live", tab["id"], {})

    def test_no_ghost_retina(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(temp)
            available = {c["id"] for c in runtime.capabilities}
            self.assertNotIn("retina.r180.step", available)
            self.assertNotIn("retina.r257.live", available)
            self.assertEqual(runtime.execute("retina.status", {})["active"], False)

    def test_heritage_integrity(self):
        obj = heritage.research_graph()
        ids = {n["id"] for n in obj["nodes"]}
        self.assertEqual(len(ids), 112)
        self.assertEqual(len(obj["edges"]), 178)
        for e in obj["edges"]:
            self.assertIn(e["source"], ids)
            self.assertIn(e["target"], ids)
