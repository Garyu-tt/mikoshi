"""Graph layout mutations with stable identity, cycle checks and safe removal."""
import uuid

AREAS = frozenset(('sidebar', 'toolbar', 'workspace', 'footer', 'drawer'))


def _tab_ids(layout):
    return {t['id'] for t in layout.state['tabs']}


def _position(area, order, column=0, row=0):
    if area not in AREAS:
        raise ValueError('Unknown display area')
    for item in (order, column, row):
        if type(item) is not int or not 0 <= item <= 4096:
            raise ValueError('Invalid layout coordinate')
    return {'area': area, 'order': order, 'column': column, 'row': row}


def add_placement(layout, action, tab, available, area='workspace', order=0, column=0, row=0):
    import re
    if not isinstance(action, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,120}', action):
        raise ValueError('Invalid action ID')
    pos = _position(area, order, column, row)
    with layout.lock:
        if action not in available:
            raise ValueError('Action unavailable')
        if tab not in _tab_ids(layout):
            raise ValueError('Tab does not exist')
        p = {'id': 'place.' + uuid.uuid4().hex[:16], 'type': 'placement',
             'source': action, 'target': tab, **pos}
        layout.state['placements'].append(p)
        layout._save()
        return p


def move_placement(layout, placement, tab, area, order=0, column=0, row=0):
    pos = _position(area, order, column, row)
    with layout.lock:
        if tab not in _tab_ids(layout):
            raise ValueError('Tab does not exist')
        found = next((p for p in layout.state['placements'] if p.get('id') == placement), None)
        if found is None:
            raise ValueError('Unknown placement')
        found.update(target=tab, **pos)
        layout._save()
        return dict(found)


def remove_placement(layout, placement):
    with layout.lock:
        before = len(layout.state['placements'])
        layout.state['placements'] = [p for p in layout.state['placements']
                                       if p.get('id') != placement]
        if before == len(layout.state['placements']):
            raise ValueError('Unknown placement')
        layout._save()
        return {'removed': placement}


def update_tab(layout, tab, title=None, parent='__keep__', order=None):
    with layout.lock:
        current = next((t for t in layout.state['tabs'] if t['id'] == tab), None)
        if current is None:
            raise ValueError('Unknown tab')
        if title is not None and (not isinstance(title, str) or
                                  not 1 <= len(title.strip()) <= 80):
            raise ValueError('Invalid tab title')
        if order is not None:
            _position('sidebar', order)
        if parent != '__keep__':
            if parent is not None and parent not in _tab_ids(layout):
                raise ValueError('Parent tab missing')
            walk = parent
            while walk is not None:
                if walk == tab:
                    raise ValueError('Tab tree cycle')
                walk = next((t['parent'] for t in layout.state['tabs']
                             if t['id'] == walk), None)
        if title is not None:
            current['title'] = title.strip()
        if order is not None:
            current['order'] = order
        if parent != '__keep__':
            current['parent'] = parent
        layout._save()
        return dict(current)

def delete_tab(layout, tab):
    with layout.lock:
        if tab not in _tab_ids(layout):
            raise ValueError('Unknown tab')
        if any(t.get('parent') == tab for t in layout.state['tabs']):
            raise ValueError('Move child tabs first')
        if any(p['target'] == tab for p in layout.state['placements']):
            raise ValueError('Remove or move buttons first')
        layout.state['tabs'] = [t for t in layout.state['tabs'] if t['id'] != tab]
        layout._save()
        return {'removed': tab}
