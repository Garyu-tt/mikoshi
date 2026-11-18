"""Retinotopic 2D bins computed ONLY from genuine measured optic axon packets."""
import hashlib
import numpy as np
from server.visual2d_validate import check


def project(eye, store, side, stride=4):
    if side not in ('left', 'right') or type(stride) is not int or not 1 <= stride <= 32:
        raise ValueError('Invalid optic 2D projection')
    if eye is None:
        raise ValueError('R239 eye is not connected')
    with eye.lock:
        r = eye.retina
        latest = store.latest()
        n = r.pixels_per_eye
        width, height, tile = r.width, r.height, r.tile
        wtiles, htiles = r.tiles_x, r.tiles_y
        groups = {}
        sequence, sha = -1, None
        if latest is not None:
            sequence, raw = latest
            sha = hashlib.sha256(raw).hexdigest()
            if len(raw) % 8:
                raise ValueError('Corrupted optic packet framing')
            spikes = np.frombuffer(raw, dtype='<u4').reshape(-1, 2)
            uids = spikes[:, 0].astype(np.int64)
            if np.any(uids >= r.optic_ganglion_count):
                raise ValueError('Unknown original optic neuron UID')
            pooled = uids < r.pooled_ganglion_count
            g = r.pooled_ganglion_count // r.tile_count
            if g <= 0 or g*r.tile_count != r.pooled_ganglion_count:
                raise ValueError('Invalid original RGC arrangement')
            tile_ids = uids[pooled] // g
            ey_pool = tile_ids // r.tiles_per_eye
            within = tile_ids % r.tiles_per_eye
            pool_x = (within % wtiles)*tile + tile//2
            pool_y = (within // wtiles)*tile + tile//2
            dense = uids[~pooled] - r.pooled_ganglion_count
            positions = np.frombuffer(r.foveal_positions, dtype=np.uint32)
            if np.any(dense//2 >= len(positions)):
                raise ValueError('Invalid foveal optic axon UID')
            loc = positions[dense//2]
            ey_dense = loc // n
            dense_x = (loc % n) % width
            dense_y = (loc % n) // width
            for ey, xs, ys in ((ey_pool,pool_x,pool_y),(ey_dense,dense_x,dense_y)):
                mask = ey == (0 if side == 'left' else 1)
                if not np.any(mask):
                    continue
                x_bins = xs[mask]//(tile*stride)
                y_bins = ys[mask]//(tile*stride)
                bx = (width + tile*stride - 1)//(tile*stride)
                merged = y_bins*bx + x_bins
                ids, counts = np.unique(merged, return_counts=True)
                for index,count in zip(ids.tolist(), counts.tolist()):
                    key = int(index % bx), int(index // bx)
                    groups[key] = groups.get(key,0) + int(count)
        max_count = max(groups.values(), default=0)
        points = [{'id':f'axon-bin.{side}.{x}.{y}',
                   'x':min(1.0,(x+.5)*tile*stride/width),
                   'y':min(1.0,(y+.5)*tile*stride/height),
                   'spike_count':count,'activity':count/max_count,
                   'type':'aggregate'} for (x,y),count in sorted(groups.items())]
        return check({'schema':'mikoshi.visual2d.v1',
            'id':'retina.axons.'+side, 'organ':'retina',
            'title':'Оптические аксоны R239: '+side,
            'projection':'retinotopic','coordinate_kind':'derived',
            'source':{'id':'retina.r239','kind':'live_retinal_spikes',
                      'body_uuid':str(eye.body),'packet_sha256':sha},
            'nodes':points,'edges':[],
            'semantics':'aggregated_actual_spike_counts_not_predicted_photons',
            'sample_sequence':sequence,'spikes_in_eye':sum(groups.values()),
            'geometry':{'width':width,'height':height,'stride':stride,'tile':tile}})
