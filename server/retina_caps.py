"""Only publish genuine sparse-retina actions when source is executable."""
import os
from server.retina_sparse import SparseRetinaR239, sparse_step
from server.spike_store import SpikeStore
from server import retina_specimen, retina_packet


def install(runtime):
    runtime.sparse = None
    runtime.spike_store = SpikeStore()
    legacy_dir = os.getenv('MIKOSHI_RETINA_LEGACY_DIR')
    if legacy_dir:
        try:
            runtime.sparse = SparseRetinaR239(legacy_dir,
                int(os.getenv('MIKOSHI_EYE_WIDTH', '920')),
                int(os.getenv('MIKOSHI_EYE_HEIGHT', '920')),
                int(os.getenv('MIKOSHI_RETINA_PASSES', '5')))
        except (ValueError, OSError, ImportError) as e:
            runtime.sparse_error = str(e)
    runtime.add('retina.sparse.status', 'Проверить R239', 'mikoshi.retina', [],
        lambda a: runtime.sparse.status() if runtime.sparse else {
            'active': False, 'reason': getattr(runtime, 'sparse_error',
            'Legacy R238/R239 source not configured')})
    if runtime.sparse is not None:
        runtime.add('retina.r239.step', 'Шаг оригинального R239', 'mikoshi.retina', [
            {'name':'epoch','type':'number'}, {'name':'phase','type':'number'},
            {'name':'sample_at_ns','type':'number'},
            {'name':'clock_domain','type':'text'},
            {'name':'left_rgb_b64','type':'text'},
            {'name':'right_rgb_b64','type':'text'}], lambda a: sparse_step(runtime, a))

        runtime.add('retina.r239.photon.accept',
            'Принять проверенный R238 пакет фоторецепторов', 'mikoshi.retina', [
            {'name':'photon_packet_b64','type':'text'},
            {'name':'clock_domain','type':'text'},
            {'name':'frame_ms','type':'number'}],
            lambda a: retina_packet.ingest(runtime, a))
        runtime.add('retina.r239.spikes.read', 'Прочитать исходные спайки R239',
            'mikoshi.retina', [
            {'name':'sequence','type':'number'},
            {'name':'offset','type':'number'}, {'name':'limit','type':'number'}],
            lambda a: runtime.spike_store.read(a))
        from server.retina_selftest import run as selftest
        runtime.add('engram.retina.r239.selftest',
            'Проверить восстановление оригинальной сетчатки R239',
            'mikoshi.retina', [], lambda a: selftest(runtime.sparse))
        runtime.add('engram.retina.r239.snapshot', 'Сохранить сетчатку R239',
            'mikoshi.engram', [{'name':'name','type':'text'}],
            lambda a: retina_specimen.snapshot(runtime, a))
        runtime.add('engram.retina.r239.preflight', 'Проверить восстановление R239',
            'mikoshi.engram', [{'name':'filename','type':'text'}],
            lambda a: retina_specimen.preflight(runtime,a))
        runtime.add('engram.retina.r239.restore', 'Восстановить сетчатку R239',
            'mikoshi.engram', [{'name':'filename','type':'text'}],
            lambda a: retina_specimen.recover(runtime, a))
