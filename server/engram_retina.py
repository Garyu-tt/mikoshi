"""Structural and semantic verification of genuine retinal specimen archives."""
import json
from server.retina_state import SCHEMA
from server.retina_state_rules import validate as validate_clocks
import uuid


def verify(z, names):
    key = 'neural/retina/state.json'
    if key not in names:
        raise ValueError('Retinal specimen missing numeric state manifest')
    state = json.loads(z.read(key))
    if not isinstance(state, dict) or state.get('schema') != SCHEMA:
        raise ValueError('Unsupported retinal specimen schema')
    validate_clocks(state)
    if str(uuid.UUID(state['body_uuid'])) != state['body_uuid']:
        raise ValueError('Invalid retinal identity representation')
    fields = state.get('fields')
    if not isinstance(fields,dict) or not fields:
        raise ValueError('Missing retinal neuron fields')
    expected = {key} | {'neural/retina/buffers/'+name+'.bin' for name in fields}
    if names != expected:
        raise ValueError('Retinal specimen has missing or unexpected numeric blobs')
    return state
