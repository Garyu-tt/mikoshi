"""Bounded viewport query over real immutable indexed neural topology."""
import json
import math
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote
from server.visual2d_validate import check

MAX_POINTS = 2500
MAX_EDGES = 6000


def connect(path):
    target = Path(path).resolve(strict=True)
    db = sqlite3.connect('file:' + quote(str(target), safe='/') + '?mode=ro', uri=True)
    db.execute('PRAGMA query_only=ON')
    return db


def info(path):
    with closing(connect(path)) as db:
        raw = db.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()
        if raw is None:
            raise ValueError('Missing 2D index metadata')
        meta = json.loads(raw[0])
        if meta.get('index_schema') != 'mikoshi.2d-index.v1':
            raise ValueError('Unknown indexed graph format')
        check({**meta, 'nodes': [], 'edges': []})
        return meta


def window(path, bounds=None, limit=1200):
    meta = info(path)
    if type(limit) is not int or not 1 <= limit <= MAX_POINTS:
        raise ValueError('Invalid viewport point limit')
    if bounds is None:
        bounds = (0., 0., 1., 1.)
    if (not isinstance(bounds, (tuple, list)) or len(bounds) != 4 or
        any(type(v) not in (int, float) or not math.isfinite(v)
            for v in bounds)):
        raise ValueError('Invalid viewport bounds')
    x0,y0,x1,y1 = bounds
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError('Viewport must lie inside the graph')
    with closing(connect(path)) as db:
        rows = db.execute('SELECT data FROM nodes WHERE x>=? AND x<=? AND '
            'y>=? AND y<=? ORDER BY x,y,id LIMIT ?',
            (x0,x1,y0,y1,limit+1)).fetchall()
        partial = len(rows) > limit
        nodes = [json.loads(r[0]) for r in rows[:limit]]
        ids = {n['id'] for n in nodes}
        edges = []
        scan_limited = False
        if ids:
            marks = ','.join('?' for _ in ids)
            cursor = db.execute('SELECT source,target,data FROM edges WHERE source IN ('+
                                marks+') ORDER BY source,target LIMIT ?',
                                [*sorted(ids), MAX_EDGES * 4 + 1])
            for scanned,(source,target,data) in enumerate(cursor):
                if scanned >= MAX_EDGES * 4 or len(edges) >= MAX_EDGES:
                    scan_limited = True; break
                if target in ids:
                    edges.append(json.loads(data))
    result = {k:v for k,v in meta.items() if k not in ('nodes_total','edges_total')}
    result.update(nodes=nodes, edges=edges,
                  window={'bounds': list(bounds), 'limit': limit,
                          'partial': partial, 'edges_partial': partial or scan_limited,
                          'total_nodes': meta['nodes_total'], 'total_edges': meta['edges_total']},
                  semantics='indexed_source_neurons_not_simulated',
                  coordinate_notice=('derived_not_anatomical' if
                    meta['coordinate_kind']=='derived' else 'source_coordinates'))
    return check(result)
