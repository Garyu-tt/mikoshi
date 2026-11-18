"""Build an immutable, indexed 2D view from owner-supplied JSONL topology."""
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path
from server.visual2d_validate import check

DDL = '''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE nodes(id TEXT PRIMARY KEY,x REAL NOT NULL,y REAL NOT NULL,data TEXT NOT NULL);
CREATE INDEX nodes_xy ON nodes(x,y,id);
CREATE TABLE edges(source TEXT NOT NULL REFERENCES nodes(id),
target TEXT NOT NULL REFERENCES nodes(id),data TEXT NOT NULL);
CREATE INDEX edges_src ON edges(source);'''


def records(path, digest):
    with Path(path).open('rb') as stream:
        for line in stream:
            digest.update(line)
            if len(line) > 4096:
                raise ValueError('JSONL record too large')
            if line.strip():
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError('JSONL records must be objects')
                yield obj


def validate_meta(meta):
    if not isinstance(meta, dict) or len(json.dumps(meta)) > 16000:
        raise ValueError('Invalid graph metadata')
    check({**meta, 'nodes': [], 'edges': []})
    if not isinstance(meta.get('title'), str) or len(meta['title']) > 120:
        raise ValueError('Invalid graph title')
    return meta


def build(meta_file, nodes_file, edges_file, output):
    meta = validate_meta(json.loads(Path(meta_file).read_text(encoding='utf8')))
    dst = Path(output).resolve()
    if dst.suffix != '.sqlite' or not dst.name.endswith('.m2d.sqlite'):
        raise ValueError('Indexed view must end in .m2d.sqlite')
    if dst.exists() or dst.is_symlink() or not dst.parent.is_dir():
        raise ValueError('Output exists or destination directory is missing')
    temp = dst.with_name('.' + uuid.uuid4().hex + '.m2d.sqlite')
    connection = None
    try:
        connection = sqlite3.connect(temp)
        os.chmod(temp, 0o600)
        connection.execute('PRAGMA foreign_keys=ON')
        connection.executescript(DDL)
        counts = [0, 0]
        digests = [hashlib.sha256(), hashlib.sha256()]
        for node in records(nodes_file, digests[0]):
            check({**meta, 'nodes': [node], 'edges': []})
            if meta['organ']=='spinal' and not str(node.get('segment','')).strip():
                raise ValueError('Spinal neuron requires source segment metadata')
            if 'x' not in node or 'y' not in node:
                raise ValueError('Indexed nodes must provide real or declared derived coordinates')
            connection.execute('INSERT INTO nodes VALUES(?,?,?,?)',
                               (node['id'], node['x'], node['y'], json.dumps(node)))
            counts[0] += 1
        for edge in records(edges_file, digests[1]):
            if not isinstance(edge.get('source'), str) or not isinstance(edge.get('target'), str):
                raise ValueError('Edge must identify existing neurons')
            connection.execute('INSERT INTO edges VALUES(?,?,?)',
                               (edge['source'], edge['target'], json.dumps(edge)))
            counts[1] += 1
        details = {**meta, 'nodes_total': counts[0], 'edges_total': counts[1],
                   'nodes_sha256': digests[0].hexdigest(),
                   'edges_sha256': digests[1].hexdigest(), 'index_schema': 'mikoshi.2d-index.v1'}
        connection.execute('INSERT INTO meta VALUES(?,?)', ('metadata', json.dumps(details)))
        if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError('Indexed graph integrity failure')
        connection.commit()
        connection.close(); connection = None
        if dst.exists():
            raise ValueError('Output already exists')
        os.link(temp, dst)  # no-overwrite: fails when destination appeared concurrently
        temp.unlink()
        return details
    finally:
        if connection is not None:
            connection.close()
        if temp.exists():
            temp.unlink()
