"""CP2M position memory and HOME regression checks; zero physical commands."""
import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]


def isolate(name, injected):
    path = ROOT / 'main.py'
    tree = ast.parse(path.read_text())
    node = next(x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == name)
    node.decorator_list = []
    ns = {'__builtins__': __builtins__, **injected}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), 'exec'), ns)
    return ns[name]


class FakeController:
    def __init__(self):
        self.idle = True
        self.calls = []

    async def check_idle_async(self, timeout=30):
        self.calls.append(('idle', timeout))
        return self.idle


class FakePatterns:
    def __init__(self, state):
        self.state = state
        self.moves = []
        self.lock = SimpleNamespace(locked=lambda: False)

    def get_pattern_lock(self):
        return self.lock

    async def move_polar(self, theta, rho, speed=None):
        self.moves.append((theta, rho, speed))
        self.state.current_theta = theta
        self.state.current_rho = rho


def harness():
    saves = []
    state = SimpleNamespace(
        conn=SimpleNamespace(is_connected=lambda: True),
        is_homing=False,
        is_homed=False,
        current_playing_file=None,
        position_reference_verified=False,
        motion_position_uncertain=False,
        last_homing_success=None,
        current_theta=1.25,
        current_rho=0.55,
        theta_calibrated=True,
        rho_calibrated=True,
        theta_revolution_units=78.000,
        rho_travel_units=51.504,
        speed=75.0,
        stop_requested=False,
        save=lambda: saves.append('saved'),
    )
    controller = FakeController()
    patterns = FakePatterns(state)
    ns = {'state':state, 'HTTPException':HTTPException, 'pattern_manager':patterns,
          'connection_manager':controller, 'logger':logging.getLogger('cp2m-test'),
          'check_homing_in_progress':lambda:None}
    ns['require_referenced_motion'] = isolate('require_referenced_motion',ns)
    return state,controller,patterns,ns,saves


def test_position_requires_verified_home_not_just_grbl_zero():
    s,c,p,ns,_=harness()
    require=ns['require_referenced_motion']
    with pytest.raises(HTTPException) as exc:
        require(full_radius=True)
    assert exc.value.status_code == 409
    assert not p.moves
    s.position_reference_verified = True
    require(full_radius=True)
    s.motion_position_uncertain = True
    with pytest.raises(HTTPException) as exc:
        require()
    assert exc.value.status_code == 409


def test_home_confirmation_does_not_move_and_requires_explicit_success():
    s,c,p,ns,saves=harness()
    ns['PhysicalHomeConfirmation'] = SimpleNamespace
    confirm = isolate('confirm_physical_home',ns)
    req=SimpleNamespace(confirmed_center=True)
    s.current_rho=0.0
    with pytest.raises(HTTPException):
        asyncio.run(confirm(req))
    assert not c.calls and not p.moves
    s.last_homing_success = True
    result = asyncio.run(confirm(req))
    assert result['physical_home_verified'] is True
    assert s.position_reference_verified and s.is_homed
    assert saves == ['saved']
    assert p.moves == []
    assert c.calls == [('idle',8)]


def test_calibration_values_preserved_and_center_perimeter_roundtrip():
    s,c,p,ns,saves=harness()
    s.position_reference_verified=True
    center=isolate('move_to_center',ns)
    outer=isolate('move_to_perimeter',ns)
    # No theta unwinding, zeroing, GRBL reset or re-teach.
    assert asyncio.run(center())['success'] is True
    assert s.current_rho == 0.0 and s.current_theta == 1.25
    assert asyncio.run(outer())['success'] is True
    assert s.current_rho == 1.0 and s.current_theta == 1.25
    assert p.moves == [(1.25, 0.0, 60.0), (1.25, 1.0, 60.0)]
    assert (s.theta_revolution_units,s.rho_travel_units) == (78.000,51.504)
    assert s.position_reference_verified and not s.motion_position_uncertain
    assert len(saves) == 2


def test_uncertain_completion_invalidates_reference_for_subsequent_patterns():
    s,c,p,ns,saves=harness()
    s.position_reference_verified=True
    c.idle=False
    with pytest.raises(HTTPException) as e:
        asyncio.run(isolate('move_to_center',ns)())
    assert e.value.status_code == 409
    assert s.motion_position_uncertain and not s.position_reference_verified
    with pytest.raises(HTTPException):
        ns['require_referenced_motion']()


def test_new_native_controls_not_old_embed_and_version_synchronized():
    from pathlib import Path
    js=(ROOT/'static/dist/oryn-v2-live.js').read_text()
    html=(ROOT/'static/dist/index.html').read_text()
    assert 'data-action="move-perimeter"' in js and 'data-action="move-center"' in js
    for token in ['confirm-home','/api/motion/confirm-home','/move_to_center','/move_to_perimeter','physical_home_verified']:
        assert token in js
    assert 'CP2M-REFERENCE-20261111' in html
    assert 'CP2M-REFERENCE-20261111' in js
    assert 'legacy.html' not in html
