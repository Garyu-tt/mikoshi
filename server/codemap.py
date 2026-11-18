"""Always-fresh AI context map. A file becomes its own graph node."""
import ast
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".py", ".js", ".gd", ".html", ".css", ".json", ".md"}
MAX_EDITABLE = 5000


def files():
    result = {}
    for p in ROOT.rglob('*'):
        if (not p.is_file() or p.is_symlink() or p.suffix not in TEXT or
            any(x.startswith('.') or x in ('__pycache__','node_modules')
                for x in p.relative_to(ROOT).parts)):
            continue
        name = p.relative_to(ROOT).as_posix()
        result[name] = (p, p.read_bytes())
    return result


def graph():
    seen = files()
    nodes, edges = [], []
    for name, (p, content) in sorted(seen.items()):
        if len(content) > MAX_EDITABLE:
            raise ValueError("File exceeds AI prompt-size contract: " + name)
        nodes.append({"id": "file:" + name, "type": "source_file", "path": name,
                      "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                      "role": name.split("/", 1)[0]})
        if p.suffix == ".js":
            for target in re.findall(r"from\s+['\"](/client/[a-zA-Z0-9_.-]+\.js)['\"]", content.decode()):
                dest = target.lstrip('/')
                if dest in seen:
                    edges.append({"source": "file:" + name,
                                  "target": "file:" + dest, "relation": "imports"})
        if p.suffix != ".py":
            continue
        try:
            tree = ast.parse(content, filename=name)
        except SyntaxError as e:
            raise ValueError("Cannot parse source " + name) from e
        for item in ast.walk(tree):
            targets = []
            if isinstance(item, ast.Import):
                targets = [a.name for a in item.names]
            elif isinstance(item, ast.ImportFrom) and item.module:
                targets = [item.module]
                targets.extend(item.module + "." + a.name for a in item.names)
            for mod in targets:
                target = mod.replace(".", "/") + ".py"
                if target in seen and target != name:
                    edges.append({"source": "file:" + name,
                                  "target": "file:" + target, "relation": "imports"})
    return {"nodes": nodes, "edges": edges,
            "schema": "mikoshi.ai-code-graph.v1", "total": len(nodes)}


def read(name):
    if not isinstance(name, str) or len(name) > 200:
        raise ValueError("Invalid file identifier")
    item = files().get(name)
    if item is None:
        raise ValueError("Unknown source graph file")
    content = item[1]
    if len(content) > MAX_EDITABLE:
        raise ValueError("Oversized source file")
    return {"path": name, "sha256": hashlib.sha256(content).hexdigest(),
            "content": content.decode("utf-8")}
