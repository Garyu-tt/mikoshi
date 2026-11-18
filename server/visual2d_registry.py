"""Live discovery of validated JSON views and immutable SQLite indexes."""
import json
from pathlib import Path
from server.visual2d_validate import check
from server.visual2d_layout import project
from server.visual2d_index_read import info, window


class Registry:
    def __init__(self, folder=None):
        self.folder = Path(folder).resolve() if folder else None

    def _iter(self):
        if self.folder is None or not self.folder.is_dir():
            return
        for path in sorted(self.folder.glob('*.json')):
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 4_000_000:
                continue
            if path.resolve().parent != self.folder:
                continue
            try:
                yield check(json.loads(path.read_text(encoding='utf-8')))
            except (ValueError, UnicodeError, OSError, KeyError, TypeError):
                continue

    def _indexed(self):
        if self.folder is None or not self.folder.is_dir():
            return
        for path in sorted(self.folder.glob('*.m2d.sqlite')):
            if path.is_symlink() or not path.is_file() or path.resolve().parent != self.folder:
                continue
            try:
                yield path, info(path)
            except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError,
                    __import__('sqlite3').DatabaseError):
                continue

    def available(self):
        seen, rows = set(), []
        for view in self._iter():
            if view['id'] in seen:
                continue
            seen.add(view['id'])
            rows.append({'id':view['id'], 'organ':view['organ'],
                         'title':view.get('title',view['id']),
                         'nodes':len(view['nodes']), 'edges':len(view['edges']),
                         'source':view['source'], 'state':'imported_read_only'})
        for path, meta in self._indexed():
            if meta['id'] in seen:
                continue
            seen.add(meta['id'])
            rows.append({'id':meta['id'], 'organ':meta['organ'],
                         'title':meta['title'], 'nodes':meta['nodes_total'],
                         'edges':meta['edges_total'], 'source':meta['source'],
                         'state':'indexed_read_only'})
        return rows

    def open(self, id_):
        for view in self._iter():
            if view['id'] == id_:
                return project(view)
        for path, meta in self._indexed():
            if meta['id'] == id_:
                return window(path)
        raise ValueError('2D source unavailable')

    def query(self, id_, args):
        coords = [args.get(k, v) for k,v in
                  (('x0',0.), ('y0',0.), ('x1',1.), ('y1',1.))]
        limit = args.get('limit', 1200)
        for path, meta in self._indexed():
            if meta['id'] == id_:
                return window(path,coords,limit)
        raise ValueError('Indexed view unavailable')
