"""Read-only motor calibration discovery, with explicit provenance."""
import json
import math
from server.motor_response import evaluate
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'heritage' / 'motor_calibrations'
SCHEMA = 'mikoshi.motor-calibration.v1'


def validate(record, filename):
    if not isinstance(record, dict) or record.get('schema') != SCHEMA:
        raise ValueError('Unsupported motor calibration schema')
    if record.get('id') != filename.stem or not filename.stem.isidentifier():
        raise ValueError('Invalid motor calibration identity')
    if not isinstance(record.get('title'), str) or not record['title']:
        raise ValueError('Motor report needs a title')
    if not isinstance(record.get('provenance'), dict):
        raise ValueError('Motor calibration missing provenance')
    if record.get('operational_status') != 'read_only_research_evidence_not_actuator':
        raise ValueError('Cannot register unknown motor control semantics')
    rows = record.get('observations')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Missing motor calibration samples')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid motor record')
        for value in row.values():
            if type(value) is float and not math.isfinite(value):
                raise ValueError('Invalid floating-point evidence')
    return record


def discover():
    if not EVIDENCE.exists():
        return []
    result=[]
    for path in sorted(EVIDENCE.glob('*.json')):
        result.append(validate(json.loads(path.read_text(encoding='utf-8')), path))
    return result


def install(runtime):
    for item in discover():
        identity = item['id']
        runtime.add('motor.calibration.'+identity+'.read', item['title'],
                    'mikoshi.motor.evidence', [], lambda a, row=item: dict(row))
        if item.get('protocol', {}).get('axis_of_torque') == 'Z':
            runtime.add('motor.calibration.'+identity+'.response',
                        'Отклик привода: '+item['title'],
                        'mikoshi.motor.evidence', [],
                        lambda a, row=item: evaluate(row))
