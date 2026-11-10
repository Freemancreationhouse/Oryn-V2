"""Real CP2L FastAPI calibration route bodies, mocked USB motors only."""
import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]


def isolate(name, injected):
    target = ROOT / 'main.py'
    tree = ast.parse(target.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    ns = dict(__builtins__=__builtins__, **injected)
    node.decorator_list = []
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(target), 'exec'), ns)
    return ns[name]


class FakeMotor:
    def __init__(self, state):
        self.s = state
        self.moves = []
        self.confirm_idle = True

    async def update_machine_position(self):
        return (self.s.machine_x, self.s.machine_y)

    async def send_grbl_coordinates(self, x, y, speed=30, timeout=30, home=True, jog_axis='y', calibration_single_attempt=False):
        assert calibration_single_attempt is True, 'calibration movement must not retry'
        self.moves.append((x, y, jog_axis, speed))
        self.s.machine_x += x
        self.s.machine_y += y
        return True

    async def check_idle_async(self, timeout=60):
        return self.confirm_idle


def fixture():
    s = SimpleNamespace(
        conn=SimpleNamespace(is_connected=lambda: True),
        is_homing=False,current_playing_file=None,current_rho=0.0,
        machine_x=0.0,machine_y=0.0,table_type='kinetiq_motion',
        rotation_calibration_active=False,rotation_calibration_start_x=None,
        rotation_calibration_current_units=0.0,
        perimeter_calibration_active=False,perimeter_calibration_start_y=None,
        perimeter_calibration_current_units=0.0,
        theta_revolution_units=70.0,theta_calibrated=True,
        rho_travel_units=50.201,rho_calibrated=True,rho_direction=1.0,
        save=lambda:None,
    )
    motor=FakeMotor(s)
    ns={'state':s, 'connection_manager':motor, 'logger':logging.getLogger('cal-test'),
        'HTTPException':HTTPException, 'RotationCalibrationJogRequest':SimpleNamespace, 'PerimeterCalibrationJogRequest':SimpleNamespace, 'check_homing_in_progress':lambda:None,
        '_save_machine_calibration_backup':lambda:None}
    return s,motor,ns


def test_theta_start_jog_reverse_save_real_handler():
    s,m,ns=fixture()
    start=isolate('start_rotation_calibration',ns)
    jog=isolate('jog_rotation_calibration',ns)
    save=isolate('save_rotation_calibration',ns)
    assert asyncio.run(start())['active'] is True
    assert s.rotation_calibration_active
    req=lambda v:SimpleNamespace(units=v,speed=30)
    asyncio.run(jog(req(.5)))
    asyncio.run(jog(req(-.2)))
    assert round(s.rotation_calibration_current_units,3)==.3
    assert m.moves==[(.5,0,'x',30),( -.2,0,'x',30)]
    assert asyncio.run(save())['theta_revolution_units']==pytest.approx(.3)
    assert not s.rotation_calibration_active and s.theta_calibrated


def test_rho_start_outward_inward_save_real_handler():
    s,m,ns=fixture()
    start=isolate('start_perimeter_calibration',ns)
    jog=isolate('jog_perimeter_calibration',ns)
    save=isolate('save_perimeter_calibration',ns)
    assert asyncio.run(start())['active'] is True
    req=lambda v:SimpleNamespace(units=v,speed=30)
    asyncio.run(jog(req(.3)))
    asyncio.run(jog(req(-.1)))
    assert m.moves==[(0,.3,'y',30),(0,-.1,'y',30)]
    assert s.perimeter_calibration_current_units==pytest.approx(.2)
    # Mock travel is below required 1.0 and must be rejected.
    with pytest.raises(HTTPException) as e:
        asyncio.run(save())
    assert e.value.status_code==400
    asyncio.run(jog(req(1.0)))
    assert asyncio.run(save())['rho_travel_units']==pytest.approx(1.2)
    assert not s.perimeter_calibration_active and s.rho_calibrated


def test_unverified_idle_never_counts_as_completed_jog():
    s,m,ns=fixture()
    asyncio.run(isolate('start_rotation_calibration',ns)())
    m.confirm_idle=False
    with pytest.raises(HTTPException) as e:
        asyncio.run(isolate('jog_rotation_calibration',ns)(SimpleNamespace(units=.5,speed=30)))
    assert e.value.status_code==409
    assert s.rotation_calibration_current_units==0.0
    assert s.rotation_calibration_active is False and s.motion_position_uncertain
    assert 'do not send another' in e.value.detail.lower()


def test_rho_rejects_noncenter_start_without_move():
    s,m,ns=fixture();s.current_rho=.3
    with pytest.raises(HTTPException) as e:
        asyncio.run(isolate('start_perimeter_calibration',ns)())
    assert e.value.status_code==409
    assert not s.perimeter_calibration_active and m.moves==[]
    assert 'true physical center' in e.value.detail
