"""Dynamic discovery of owner-provided executable neural datasets."""
import json
import os
from pathlib import Path
from server.connectome_engine import Connectome
from server import specimen

PREFIX = ('connectome.status.', 'connectome.step.',
          'engram.snapshot.', 'engram.restore.')


def discover(runtime):
    folder = runtime.connectome_dir
    if folder is None:
        return {}
    if not folder.is_dir():
        previous = {k:v for k,v in runtime.connectomes.items() if v.tick}
        for engine in previous.values():
            engine.source_detached = True
        return previous
    found = {}
    for path in sorted(folder.glob('*.connectome.json')):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            raw = path.read_bytes()
            parsed = json.loads(raw)
            if not path.name == parsed['id']+'.connectome.json':
                continue
            key = parsed['id']
            prev = runtime.connectomes.get(key)
            engine = prev if prev and prev.source_bytes == raw else Connectome(parsed,raw)
            if engine is prev:
                engine.source_detached = False
            # A changed source never replaces an executing graph without explicit restart.
            if prev and prev.source_bytes != raw and prev.tick:
                prev.source_detached = True
                found[key] = prev
            else:
                found[key] = engine
        except (ValueError, KeyError, OSError, TypeError, UnicodeError):
            continue
    for key, previous in runtime.connectomes.items():
        if key not in found and previous.tick:
            previous.source_detached = True
            found[key] = previous  # keep recoverable state until checkpoint
    return found


def sync(runtime):
    runtime.connectomes = discover(runtime)
    wanted = set()
    for key, engine in runtime.connectomes.items():
        actions = [
            ('connectome.status.'+key,'Статус коннектома',[],lambda a,k=key:runtime.connectomes[k].status()),
            ('connectome.step.'+key,'Исполнить нейронный такт',[
                {'name':'sample_at_ns','type':'number'},
                {'name':'clock_domain','type':'text'},
                {'name':'pulses','type':'json'}],lambda a,k=key:run_step(runtime,runtime.connectomes[k],a)),
            ('engram.snapshot.'+key,'Сохранить нейронную энграмму',[
                {'name':'name','type':'text'}],lambda a,k=key:specimen.snapshot(runtime,runtime.connectomes[k],a)),
            ('engram.restore.'+key,'Восстановить нейронную энграмму',[
                {'name':'filename','type':'text'}],lambda a,k=key:specimen.recover(runtime,runtime.connectomes[k],a))]
        for name,title,fields,fn in actions:
            wanted.add(name)
            if name not in runtime.handlers:
                runtime.add(name,title,'mikoshi.connectome',fields,fn)
    for name in list(runtime.handlers):
        if name.startswith(PREFIX) and name not in wanted:
            del runtime.handlers[name]
    runtime.capabilities[:] = [c for c in runtime.capabilities if
                               not c['id'].startswith(PREFIX) or c['id'] in wanted]


def run_step(runtime, engine, args):
    with engine.lock:
        result = engine.step(args)
        runtime.bus.publish('connectome.'+engine.id, 'neural.spikes', result['source_sequence'],
                            result['sample_at_ns'],
                            {'count':len(result['spike_ids']), 'tick':result['tick'],
                             'source_sha256':engine.source_sha256},result['clock_domain'])
    return result


def install(runtime):
    name = os.getenv('MIKOSHI_CONNECTOME_DIR')
    runtime.connectome_dir = Path(name).resolve() if name else None
    runtime.connectomes = {}
    sync(runtime)
