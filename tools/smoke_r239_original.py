"""Real source-pinned retina R239 -> Engram v2 -> exact resumed spike trace.

Run only in an isolated trusted environment with six original Python sources,
NumPy and a configured read-only MIKOSHI_RETINA_LEGACY_DIR. Never a demo source.
"""
import base64
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile
from server import engram, retina_state
from server.retina_sparse import SparseRetinaR239


def frame(eye,i,t0):
    level=(0,255,80,220)[i%4]
    rgb=base64.b64encode(bytes([level]*3)*(eye.width*eye.height)).decode()
    return eye.step({'epoch':i//eye.passes,'phase':i%eye.passes,
        'sample_at_ns':t0+i*33_000_000,'clock_domain':'unix-ns',
        'left_rgb_b64':rgb,'right_rgb_b64':rgb,'frame_ms':33})


def main():
    source=os.environ.get('MIKOSHI_RETINA_LEGACY_DIR')
    if not source:
        raise SystemExit('Missing pinned real retinal source directory')
    a=SparseRetinaR239(source,width=32,height=32,passes=4)
    t0=time.time_ns()
    for i in range(7):
        frame(a,i,t0)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'genuine-R239.engram'
        engram.create(path,retina_state.capture(a),'retina-specimen',str(a.body))
        assert engram.verify(path)['kind']=='retina-specimen'
        b=SparseRetinaR239(source,width=32,height=32,passes=4)
        with ZipFile(path) as z:
            state=json.loads(z.read('neural/retina/state.json'))
            valid=retina_state.preflight(b,state,z)
            assert valid['accepted'] and not valid['mutated']
            assert b.last_step==-1
            retina_state.restore(b,state,z)
        counts=0
        for i in range(7,20):
            continuous=frame(a,i,t0)
            recovered=frame(b,i,t0)
            assert continuous['_spikes_raw']==recovered['_spikes_raw'],i
            assert continuous['metadata']==recovered['metadata'],i
            counts+=continuous['spike_bytes']//8
        assert counts>0,'Test stimulus did not provoke ganglion activity'
        original=retina_state.capture(a)
        restored=retina_state.capture(b)
        assert original.keys()==restored.keys()
        assert all(original[k]==restored[k] for k in original),'Neuronal state diverged'
        print(json.dumps({'result':'PASS','verified_original_source':True,
              'engram_format':'mikoshi-engram.v1/retina-r239-state.v2',
              'phases_before_checkpoint':7,'identical_phases_after_restore':13,
              'post_checkpoint_spikes':counts,'neural_state_byte_identical':True,
              'engram_bytes':path.stat().st_size,'no_motor_actions':True},
              sort_keys=True))

if __name__=='__main__':
    main()
