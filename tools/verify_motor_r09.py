"""Validate acquired calibration reports without simulating motor output."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from server.motor_registry import discover


def main():
    records = {item['id']:item for item in discover()}
    z = records['r185_lateral_z']
    points = {s['torque_n_m']:s for s in z['observations']}
    assert set(points)=={0,-2,2}
    assert all(x['left_foot_contact_frames']==x['right_foot_contact_frames']==90
               for x in points.values())
    assert points[-2]['velocity_right_m_s'] > points[0]['velocity_right_m_s']
    assert points[2]['velocity_right_m_s'] < points[0]['velocity_right_m_s']
    assert all(r['operational_status']=='read_only_research_evidence_not_actuator'
               for r in records.values())
    print('PASS: separate R185 evidence preserved, no actuator action')


if __name__=='__main__': main()
