"""Composable manifest fragments, no central hardcoded list of modules."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build():
    nodes, edges = [], []
    for path in sorted((ROOT/'graph').glob('modules*.json')):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if manifest.get('schema', manifest.get('version')) != 'mikoshi.module-graph.v1':
            raise ValueError('Incompatible module graph fragment')
        nodes.extend(manifest['nodes'])
        edges.extend(manifest['edges'])
    ids = {n['id'] for n in nodes}
    if len(ids) != len(nodes) or any(e['source'] not in ids or e['target'] not in ids for e in edges):
        raise ValueError('Dangling or duplicate architecture node')
    return {'version':'mikoshi.module-graph.v1', 'nodes':nodes,'edges':edges}
