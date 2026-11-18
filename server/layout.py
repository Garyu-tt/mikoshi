"""Persistent graph placements. Actions are IDs, never hand-coded menu items."""
import json
import os
import re
import threading
import uuid
from pathlib import Path
from server import layout_ops

_ID = re.compile(r"^[a-zA-Z0-9_.-]{1,120}$")


class Layout:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.state = {"version": 1, "tabs": [], "placements": []}
        if self.path.exists():
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            if obj.get("version") != 1 or not isinstance(obj.get("tabs"), list):
                raise ValueError("Invalid layout version")
            if not isinstance(obj.get("placements"), list):
                raise ValueError("Invalid placements")
            self.state = obj

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name("." + self.path.name + "." + uuid.uuid4().hex + ".new")
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        finally:
            if tmp.exists():
                tmp.unlink()

    def tab(self, title, parent=None):
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
            raise ValueError("Tab title must have 1..80 characters")
        with self.lock:
            if len(self.state["tabs"]) >= 128:
                raise ValueError("Tab quota exceeded")
            if parent is not None and parent not in {t["id"] for t in self.state["tabs"]}:
                raise ValueError("Parent tab missing")
            tab = {"id": "tab." + uuid.uuid4().hex[:12], "type": "tab",
                   "title": title.strip(), "parent": parent, "order": len(self.state["tabs"])}
            self.state["tabs"].append(tab)
            self._save()
            return tab

    def place(self, action, tab, available, order=0, area="workspace", column=0, row=0):
        return layout_ops.add_placement(self, action, tab, available,
                                        area, order, column, row)

    def move(self, placement, tab, area="workspace", order=0, column=0, row=0):
        return layout_ops.move_placement(self, placement, tab, area, order, column, row)

    def remove(self, placement):
        return layout_ops.remove_placement(self, placement)

    def update_tab(self, tab, title=None, parent="__keep__", order=None):
        return layout_ops.update_tab(self, tab, title, parent, order)

    def delete_tab(self, tab):
        return layout_ops.delete_tab(self, tab)

    def graph(self, capabilities):
        with self.lock:
            available = {c["id"]: c for c in capabilities}
            tabs = [dict(t) for t in self.state["tabs"]]
            owners = sorted({c["owner"] for c in capabilities})
            acts = [{"id": c["id"], "type": "action", "title": c["title"],
                     "owner": c["owner"], "fields": c.get("fields", [])}
                    for c in capabilities]
            places = [dict(p) for p in self.state["placements"] if p["source"] in available]
            nodes = tabs + acts + [{"id": "module:"+o, "type": "module", "title": o}
                                   for o in owners]
            nodes += [{**p, "type": "button", "action": p["source"], "tab": p["target"]}
                      for p in places]
            edges = places + [{"source": "module:"+c["owner"], "target": c["id"],
                               "relation": "provides"} for c in capabilities]
            edges += [{"source": t["parent"], "target": t["id"], "relation": "child"}
                      for t in tabs if t.get("parent") is not None]
            return {"schema": "mikoshi.layout-graph.v2", "nodes": nodes,
                    "edges": edges, "placements": places,
                    "areas": sorted(layout_ops.AREAS),
                    "unplaced": [c["id"] for c in capabilities if not any(
                        p["source"] == c["id"] for p in places)],
                    "hidden_unavailable_placements": sum(
                        p["source"] not in available for p in self.state["placements"])}
