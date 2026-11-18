"""Physics QA response from measured R185 points, never actuator output."""
import math


def evaluate(record):
    protocol = record.get('protocol', {})
    rows = record.get('observations', [])
    if protocol.get('axis_of_torque') != 'Z' or (
            protocol.get('velocity_axis') != 'right_positive'):
        raise ValueError('No signed Z-response data in this report')
    values = {}
    for row in rows:
        x, y = row.get('torque_n_m'), row.get('velocity_right_m_s')
        if (type(x) not in (int, float) or type(y) not in (int, float) or
                not math.isfinite(x) or not math.isfinite(y) or x in values):
            raise ValueError('Invalid or duplicate Z torque observation')
        values[x] = y
    if len(values) < 3 or 0 not in values:
        raise ValueError('At least 3 measured torques, including neutral, required')
    coords = sorted(values.items())
    segments = []
    for (a, va), (b, vb) in zip(coords, coords[1:]):
        segments.append({'torque_from_n_m': a, 'torque_to_n_m': b,
                         'delta_v_per_n_m': (vb-va)/(b-a)})
    contact = protocol.get('frames')
    all_contact = type(contact) is int and contact > 0 and all(
        r.get('left_foot_contact_frames') == contact and
        r.get('right_foot_contact_frames') == contact for r in rows)
    return {'schema':'mikoshi.motor-response-evidence.v1',
            'source_id':record['id'], 'provenance':record['provenance'],
            'observed_torque_range_n_m':[coords[0][0],coords[-1][0]],
            'neutral_velocity_m_s':values[0], 'segments':segments,
            'both_feet_contact_for_each_reported_frame':all_contact,
            'samples':len(rows), 'extrapolation_allowed':False,
            'motor_command_available':False, 'learned_balance_verified':False}
