"""Dynamic IDE capability registry."""
import os
import re
from pathlib import Path
from server import engram, action_args
from server.layout import Layout
from server.ide_controls import install as install_ide
from server.snapshots import install as install_snapshots
from server.bus import NeuralBus
from server.nervous import install_nervous
from server.retina import RetinaR180
from server.retina_caps import install as install_sparse_retina
from server.visual2d_caps import install as install_visual2d, sync as sync_visual2d
from server.connectome_caps import install as install_connectome, sync as sync_connectome
from server import motor_registry
from server.recursive_catalog import Catalog
from server.recursive_api import install as install_recursive
from server.runtime_ide import install as install_runtime_ide

NAME = re.compile(r"^[a-zA-Z0-9_.-]{1,100}$")


class Runtime:
    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)
        self.layout = Layout(self.state_dir / "layout.json")
        self.bus = NeuralBus()
        self.vault = self.state_dir / "engrams"
        self.handlers = {}
        self.capabilities = []
        self.components = Catalog(Path(__file__).resolve().parent.parent / "units",
                                  self.state_dir / "components.json")
        self.retina = None
        source = os.environ.get("MIKOSHI_RETINA_R180")
        if source:
            try:
                self.retina = RetinaR180(source,
                    int(os.getenv("MIKOSHI_EYE_WIDTH", "920")),
                    int(os.getenv("MIKOSHI_EYE_HEIGHT", "920")))
            except (ValueError, OSError, ImportError) as e:
                self.retina_error = str(e)
        install_ide(self)
        install_runtime_ide(self)
        install_nervous(self)
        motor_registry.install(self)
        self.add("retina.status", "Статус сетчатки", "mikoshi.retina", [],
                 lambda a: self.retina.status() if self.retina else {
                     "active": False, "reason": getattr(self, "retina_error",
                     "Original source not configured"), "source": "R180"})
        install_sparse_retina(self)
        install_connectome(self)
        install_visual2d(self)
        install_snapshots(self)
        install_recursive(self)
        self.add("engram.list", "Каталог энграмм", "mikoshi.engram", [],
                 lambda a: {"engrams": [p.name for p in self.vault.glob("*.engram")]
                             if self.vault.exists() else []})
        self.add("engram.verify", "Проверить энграмму", "mikoshi.engram",
                 [{"name": "filename", "label": "Имя файла", "type": "text"}],
                 self._engram_verify)
        if self.retina is not None:
            self.add("retina.r180.step", "Шаг Retina R180", "mikoshi.retina",
                     [{"name": "frame_id", "type": "number"},
                      {"name": "sample_at_ns", "type": "number"},
                      {"name": "clock_domain", "type": "text"},
                      {"name": "left_rgb_b64", "type": "text"},
                      {"name": "right_rgb_b64", "type": "text"}],
                     self._retina_step)

    def _retina_step(self, args):
        result = self.retina.step(args)
        self.bus.publish("retina.r180", "optic.spikes.summary",
            result["metadata"]["frame_id"], result["sample_at_ns"],
            {"spikes": result["metadata"]["spikes"],
             "sha256": result["spikes_sha256"]}, result["clock_domain"])
        return result

    def add(self, id_, title, owner, fields, fn):
        if id_ in self.handlers:
            raise ValueError("Duplicate capability")
        self.handlers[id_] = fn
        self.capabilities.append({"id": id_, "title": title, "owner": owner,
                                  "fields": fields, "available": True,
                                  "api": "/api/v1/action"})

    def _engram_verify(self, args):
        filename = args.get("filename")
        if not isinstance(filename, str) or not NAME.fullmatch(filename):
            raise ValueError("Unsafe file name")
        return engram.verify(self.vault / filename)

    def update_views(self):
        sync_connectome(self)
        sync_visual2d(self)

    def visible_capabilities(self):
        return self.components.actions(self.capabilities)

    def execute(self, action, args):
        self.update_views()
        if action not in {c["id"] for c in self.visible_capabilities()}:
            raise ValueError("Unknown or unavailable capability")
        args = action_args.normalize(self.visible_capabilities(), action, args)
        return self.handlers[action](args)
