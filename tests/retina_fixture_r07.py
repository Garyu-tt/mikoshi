"""Tiny structural test double. Never presented as a historical retina."""
from array import array
from types import SimpleNamespace
import threading
import uuid
import numpy as np


def fake_eye():
    body = uuid.uuid4()
    retina = SimpleNamespace(tile=8, _type_count=[[1,2],[3,4]],
        baseline=bytearray([4,8,12]), photocurrent=bytearray([11,13,15]),
        horizontal=array('f',[1.25,3.5]),
        bipolar_on=array('f',[-2.25,4.0]),
        _lut=np.arange(8,dtype=np.int16),
        last_frame_id=2, frame_count=2,_count_total=0)
    sensor = SimpleNamespace(valid=np.array([True,False,True]),
        last_observed_ns=np.array([100, -1, 100],dtype=np.int64),
        last_step=1, last_capture_ns=100, expected_body=body)
    sampler = SimpleNamespace(seed=228, _epoch=0,
        _phase_map=np.array([0,1],dtype=np.uint8),_ids=[np.array([0])])
    circuit = SimpleNamespace(sensor=sensor,
        _old_mean=np.array([0.33,-0.5],dtype=np.float64),
        _last_tile_ns=np.array([100,0],dtype=np.int64),
        _current_mosaic=np.frombuffer(retina.baseline,dtype=np.uint8))
    return SimpleNamespace(retina=retina,sampler=sampler,circuit=circuit,
        body=body,width=16,height=16,passes=5,last_step=1,
        lock=threading.RLock(),source_folder='/path/not-read-in-test')


def blank_eye():
    obj=fake_eye()
    obj.last_step = -1
    obj.circuit.sensor.last_step=-1
    obj.circuit.sensor.last_capture_ns=0
    obj.body = uuid.uuid4()
    obj.circuit.sensor.expected_body=obj.body
    obj.retina.horizontal[:]=array('f',[0,0])
    obj.retina.photocurrent[:]=b'\0\0\0'
    return obj
