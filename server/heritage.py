"""Read-only, explicit historical-provenance and graph queries."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def research_graph():
    base = ROOT / "heritage" / "graph"
    nodes, edges = [], []
    for file in sorted(base.glob("nodes_*.json")):
        nodes.extend(json.loads(file.read_text(encoding="utf-8")))
    for file in sorted(base.glob("edges_*.json")):
        edges.extend(json.loads(file.read_text(encoding="utf-8")))
    return {"nodes": nodes, "edges": edges, "source": "historical_reported"}


def inventory():
    return json.loads((ROOT / "heritage" / "source_inventory.json").read_text())


def lookup(query):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError("Query maximum is 100 characters")
    q = query.casefold()
    data = research_graph()
    nodes = [n for n in data["nodes"] if q in (n.get("id", "") + " " +
             n.get("label", "") + " " + n.get("description", "")).casefold()]
    ids = {n["id"] for n in nodes}
    return {"nodes": nodes[:50], "edges": [e for e in data["edges"] if
            e["source"] in ids or e["target"] in ids][:100],
            "total_matches": len(nodes), "source": "historical_reported"}
