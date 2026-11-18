"""Create honest research Engrams: metadata only, no invented neural state."""
import json
import re
import time
from pathlib import Path
from server import engram, codemap, heritage, graph_union, buildinfo, motor_registry

ROOT = Path(__file__).resolve().parent.parent
VALID = re.compile(r'^[a-zA-Z0-9_.-]{1,90}$')


def capture(runtime, args):
    name = args.get('name')
    if not isinstance(name, str) or not VALID.fullmatch(name):
        raise ValueError('Name must be a safe file stem')
    layout = runtime.layout.graph(runtime.visible_capabilities())
    structure = graph_union.build(runtime)
    pins = (ROOT/'heritage/retina_source_pins.json').read_bytes()
    meta = {'schema':'mikoshi.research.snapshot.v1',
            'created_at_unix_ns': time.time_ns(), 'neural_state_present': False,
            'vision_r257_gate': 'blocked_for_production',
            'retina_r239_active': runtime.sparse is not None}
    encode = lambda obj: json.dumps(obj,ensure_ascii=False,sort_keys=True).encode('utf-8')
    blobs = {'research/summary.json':encode(meta),
             'research/retina_source_pins.json':pins,
             'research/ui_graph.json':encode(layout),
             'research/code_graph.json':encode(codemap.graph()),
             'research/architecture_graph.json':encode(structure),
             'research/history_graph.json':encode(heritage.research_graph()),
             'research/visual2d_views.json':encode(runtime.visual2d_views)}
    for record in motor_registry.discover():
        key='research/motor_calibrations/'+record['id']+'.json'
        blobs[key] = (motor_registry.EVIDENCE/(record['id']+'.json')).read_bytes()
    path = runtime.vault / (name + '.engram')
    if path.exists():
        raise ValueError('Engram already exists, never silently overwrite')
    engram.create(path, blobs,kind='research',identity='Mikoshi research '+buildinfo.version())
    return {'created':path.name, **engram.verify(path)}


def install(runtime):
    runtime.add('engram.snapshot_research', 'Сохранить исследовательскую энграмму',
        'mikoshi.engram', [{'name':'name','label':'Имя','type':'text'}],
        lambda a: capture(runtime,a))
