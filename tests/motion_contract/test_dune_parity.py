"""Offline proof that the extracted motion transform matches Dune Weaver math.

Run: python -m pytest -q tests/motion_contract
"""
import math
from pathlib import Path
import pytest
from modules.core.kinematics_contract import dune_coupled_delta


def reference(delta_theta, delta_rho, *, x_steps, y_steps, gear_ratio, mini=False):
    # Independently lifted from original dune-weaver-main pattern_manager.py.
    xs = 2
    ys = 3.7 if mini else 5
    dx = delta_theta * 100 / (2 * math.pi * xs)
    dy = delta_rho * 100 / ys
    x_total_steps = x_steps * (100 / xs)
    y_total_steps = y_steps * (100 / ys)
    offset = dx * (x_total_steps * xs / (gear_ratio * y_total_steps * ys))
    if mini or y_steps == 546:
        dy -= offset
    else:
        dy += offset
    return dx, dy

@pytest.mark.parametrize('theta,rho', [(2*math.pi,0),(math.pi,.3),(-.25*math.pi,-.5),(25*math.pi,.03),(-11*math.pi,-1)])
@pytest.mark.parametrize('kind,xsteps,ysteps,gear', [('kinetiq_motion',320,287,10),('kinetiq_motion_mini',256,180,6.25),('kinetiq_motion_gold',200,270,6.25),('kinetiq_motion',256,546,10)])
def test_original_dune_weaver_parity(theta,rho,kind,xsteps,ysteps,gear):
    actual = dune_coupled_delta(theta,rho,x_steps=xsteps,y_steps=ysteps,gear_ratio=gear,table_type=kind)
    expected = reference(theta,rho,x_steps=xsteps,y_steps=ysteps,gear_ratio=gear,mini=kind=='kinetiq_motion_mini')
    assert (actual.x,actual.y) == pytest.approx(expected,abs=1e-10)

def test_calibrated_25_turns_coupled_and_returns_without_math_drift():
    x=y=0
    previous_theta=0
    previous_rho=1
    first_x=first_y=0
    for i in range(1,1001):
        theta=math.tau*25*i/1000
        rho=1-.96*i/1000
        p=dune_coupled_delta(theta-previous_theta,rho-previous_rho,x_steps=256,y_steps=210,gear_ratio=6.25,
                              theta_revolution_units=42.0,rho_travel_units=26,rho_direction=1.0)
        x+=p.x; y+=p.y
        previous_theta,previous_rho=theta,rho
        assert math.isfinite(x) and math.isfinite(y)
    assert x == pytest.approx(1050.0,abs=1e-7)
    assert y == pytest.approx((-0.96*26)+(1050*256/(6.25*210)),abs=1e-7)
    # Reverse logical motion must take the mathematical controller position back.
    back=dune_coupled_delta(-previous_theta,1-previous_rho,x_steps=256,y_steps=210,gear_ratio=6.25,
                            theta_revolution_units=42.0,rho_travel_units=26)
    assert x+back.x == pytest.approx(first_x,abs=1e-7)
    assert y+back.y == pytest.approx(first_y,abs=1e-7)

@pytest.mark.parametrize('bad', [0,-1,float('nan'),float('inf')])
def test_bad_calibration_stops_before_any_motor_command(bad):
    with pytest.raises(ValueError):
        dune_coupled_delta(1,.2,x_steps=256,y_steps=bad,gear_ratio=6.25)

@pytest.mark.parametrize('filename', ['clear_from_in.thr','clear_from_out.thr','clear_from_out_pro.thr','clear_from_in_Ultra.thr'])
def test_original_cleaning_coordinate_ranges(filename):
    root=Path(__file__).resolve().parents[2] / 'patterns'
    lines=[line.strip() for line in (root / filename).read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
    assert len(lines)>1000
    points=[tuple(map(float,l.split()[:2])) for l in lines]
    assert all(math.isfinite(t) and 0 <=r<=1 for t,r in points)
    assert abs(points[-1][0]-points[0][0]) > math.tau*10

# Simulate the exact _send_grbl_coupled_delta_sync method from the production
# controller, without importing serial-dependent hardware modules.
def _load_actual_coupled_sender():
    import ast
    import os
    import time as real_time
    import types
    import logging
    import contextlib
    root = Path(__file__).resolve().parents[2]
    module = ast.parse((root / 'modules/core/pattern_manager.py').read_text())
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'MotionControlThread')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_send_grbl_coupled_delta_sync')
    isolated = ast.Module(body=[ast.ClassDef(name='Control', bases=[], keywords=[], body=[method], decorator_list=[])], type_ignores=[])
    ast.fix_missing_locations(isolated)
    container = {'contextlib': contextlib, 'logger': logging.getLogger('aryon-test'), 'time': real_time, 'os': os}
    exec(compile(isolated,'oryn_pattern_manager_motion_method','exec'),container)
    return container['Control'], container


def test_unknown_ack_cannot_mark_relative_move_accepted(monkeypatch):
    import types
    Control, mod = _load_actual_coupled_sender()
    class Controller:
        def __init__(self):self.sent=[]
        def is_connected(self):return True
        def send(self, message):self.sent.append(message)
        def readline(self):return '<Run|MPos:10,1,0>'
    conn=Controller()
    state=types.SimpleNamespace(stop_requested=False,conn=conn,last_motion_error=None)
    mod['state']=state
    real=mod['time']
    clock=types.SimpleNamespace(n=0.0)
    def advancing_time():
        clock.n+=5
        return clock.n
    monkeypatch.setitem(mod,'time',types.SimpleNamespace(time=advancing_time))
    ok=Control()._send_grbl_coupled_delta_sync(2.3,0.8,50)
    assert ok is False
    assert state.stop_requested is True
    assert state.last_motion_error=='relative_ack_unknown'
    assert state.motion_position_uncertain is True
    assert conn.sent[0].startswith('G91 G21 G1')
    assert conn.sent[-1]=='!'  # Feed hold on uncertain acceptance.
    assert sum(cmd.startswith('G91') for cmd in conn.sent)==1  # No dangerous resend.


def test_explicit_ok_allows_single_relative_move():
    import types
    Control, mod = _load_actual_coupled_sender()
    class Controller:
        def __init__(self):self.sent=[]
        def is_connected(self):return True
        def send(self,msg):self.sent.append(msg)
        def readline(self):return 'ok'
    controller=Controller()
    mod['state']=types.SimpleNamespace(stop_requested=False,conn=controller)
    assert Control()._send_grbl_coupled_delta_sync(4.0,0.4,30) is True
    assert len(controller.sent)==1
    assert controller.sent[0].startswith('G91 G21 G1 X4.000000 Y0.400000')
