"""Lossless-count 2D LOD of genuinely observed R239 photo-receptors."""
from server.visual2d_validate import check


def project(retina_runtime, eye, stride=4):
    if eye not in ('left','right') or type(stride) is not int or not 1 <= stride <= 32:
        raise ValueError('Invalid eye or LOD stride')
    r = retina_runtime
    if r is None:
        raise ValueError('Real R239 retina is not connected')
    with r.lock:
        import numpy as np
        sensor = r.circuit.sensor
        width,height,tile = r.width,r.height,r.retina.tile
        n = width*height
        offset = 0 if eye == 'left' else n
        stamps = sensor.last_observed_ns[offset:offset+n].reshape(height,width)
        observed = sensor.valid[offset:offset+n].reshape(height,width)
        htiles, wtiles = height//tile,width//tile
        count = observed.reshape(htiles,tile,wtiles,tile).sum(axis=(1,3))
        latest = stamps.reshape(htiles,tile,wtiles,tile).max(axis=(1,3))
        # Freshness is derived only from truly observed receptors in this capture.
        fresh = (observed & (stamps == sensor.last_capture_ns))
        fresh = fresh.reshape(htiles,tile,wtiles,tile).sum(axis=(1,3))
        points=[]
        for ty in range(0,htiles,stride):
            for tx in range(0,wtiles,stride):
                y1,x1=min(ty+stride,htiles),min(tx+stride,wtiles)
                observed_total=int(count[ty:y1,tx:x1].sum())
                if not observed_total:
                    continue
                capacity=(y1-ty)*(x1-tx)*tile*tile
                freshly_observed=int(fresh[ty:y1,tx:x1].sum())
                points.append({'id':f'tile.{eye}.{tx}.{ty}',
                    'x':(tx+x1)*tile/(2*width),
                    'y':(ty+y1)*tile/(2*height),
                    'observed_fraction':observed_total/capacity,
                    'sampled_receptors':observed_total,
                    'fresh_receptors':freshly_observed,
                    'receptor_capacity':capacity,
                    'last_observed_ns':int(latest[ty:y1,tx:x1].max()),
                    'fresh_now':freshly_observed>0})
        return check({'schema':'mikoshi.visual2d.v1','id':f'retina.{eye}',
            'organ':'retina','title':f'Retina R239 {eye}',
            'projection':'retinotopic','coordinate_kind':'source',
            'source':{'id':'retina.r239','body_uuid':str(r.body),
                      'kind':'real_photon_history'},
            'nodes':points,'edges':[],
            'geometry':{'width':width,'height':height,'tile':tile,
                        'stride':stride,'eye':eye},
            'semantics':'observed_receptor_density_not_irradiance',
            'last_step':r.last_step})
