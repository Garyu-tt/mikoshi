"""Coherence checks for exact historical R239 neuron-state checkpoints."""

def validate(state):
    if not isinstance(state, dict):
        raise ValueError('Invalid retina state')
    scalars = state.get('scalars')
    if not isinstance(scalars, dict):
        raise ValueError('Missing retina clocks')
    step = state.get('last_step')
    if type(step) is not int or step < -1:
        raise ValueError('Invalid retinal phase index')
    expected = {
        'sensor.last_step': step,
        'retina.last_frame_id': step + 1 if step >= 0 else -1,
        'retina.frame_count': step + 1,
    }
    for key, value in expected.items():
        if type(scalars.get(key)) is not int or scalars[key] != value:
            raise ValueError('Inconsistent original R239 counter: ' + key)
    if type(scalars.get('retina._count_total')) is not int or (
            scalars['retina._count_total'] < 0):
        raise ValueError('Invalid retinal aggregate counter')
    ns = scalars.get('sensor.last_capture_ns')
    if type(ns) is not int or (step == -1 and ns != 0) or (step >= 0 and ns <= 0):
        raise ValueError('Inconsistent source observation clock')
    passes = state.get('passes')
    if passes not in (4, 5) or (step >= 0 and step // passes >= 2**32):
        raise ValueError('Retinal source sample index overflow')
    return state
