"""CP2N regression: no physical serial commands, preservation of calibration & guardrails."""
import ast
import asyncio
import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]


def isolate(rel, name, injected):
    src = ROOT / rel
    tree = ast.parse(src.read_text())
    node = next(x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == name)
    node.decorator_list = []
    ns = {'__builtins__': __builtins__, **injected}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(src), 'exec'), ns)
    return ns[name]


def test_endpoint_rejects_drift_and_revokes_reference():
    s = SimpleNamespace(machine_x=14.0, machine_y=26.0, position_reference_verified=True,
                        motion_position_uncertain=False, stop_requested=False, last_motion_error=None)
    fn = isolate('modules/core/pattern_manager.py', '_confirm_controller_endpoint',
                 {'state': s, 'logger': logging.getLogger('cp2n-test')})
    assert fn((14.05, 25.98), context='pattern entry')
    assert s.position_reference_verified
    assert s.last_position_check == 'passed'
    assert not fn((14.0, 23.0), context='pattern finish')
    assert not s.position_reference_verified and s.motion_position_uncertain
    assert s.stop_requested
    assert s.last_motion_error == 'controller_endpoint_mismatch'
    assert 'pattern finish' in s.last_position_check


def test_endpoint_requires_reported_position_even_if_planner_accepted():
    s = SimpleNamespace(machine_x=None, machine_y=None, position_reference_verified=True,
                        motion_position_uncertain=False, stop_requested=False)
    fn = isolate('modules/core/pattern_manager.py', '_confirm_controller_endpoint',
                 {'state': s, 'logger': logging.getLogger('cp2n-test')})
    assert not fn((1, 2), context='pattern entry')
    assert not s.position_reference_verified and s.motion_position_uncertain


def fixture(tmp_path):
    patterns = tmp_path / 'patterns'
    patterns.mkdir()
    (patterns / 'star.thr').write_text('0 0\n1 1\n')
    (patterns / 'wave.thr').write_text('0 0\n1 1\n')
    (tmp_path / 'outside.thr').write_text('0 0\n1 1\n')
    s = SimpleNamespace(
        conn=SimpleNamespace(is_connected=lambda: True),
        position_reference_verified=True, motion_position_uncertain=False,
        current_playlist=['./patterns/star.thr'], current_playlist_index=0,
        current_playing_file='./patterns/star.thr', playlist_mode='single',
        current_theta=0, current_rho=0, theta_revolution_units=78.000, rho_travel_units=51.504,
        gear_ratio=10,
    )
    lock = SimpleNamespace(locked=lambda: True)
    pm = SimpleNamespace(THETA_RHO_DIR=str(patterns), get_pattern_lock=lambda: lock)
    ns = dict(
        state=s, os=os, pattern_manager=pm, HTTPException=HTTPException,
        normalize_file_path=lambda name: name.removeprefix('./patterns/').removeprefix('patterns/'),
        logger=logging.getLogger('cp2n-test'),
        NextUpRequest=SimpleNamespace, RemoveNextUpRequest=SimpleNamespace,
    )
    return s, lock, ns


def test_queue_inserts_only_after_current_without_serial_commands(tmp_path):
    s, lock, ns = fixture(tmp_path)
    route = isolate('main.py', 'queue_next_pattern', ns)
    result = asyncio.run(route(SimpleNamespace(file_name='wave.thr')))
    assert result['success'] is True
    assert result['pending'] == ['wave.thr']
    assert s.current_playlist_index == 0
    assert s.current_playlist[-1].endswith('/wave.thr')
    assert (s.theta_revolution_units, s.rho_travel_units, s.gear_ratio) == (78, 51.504, 10)
    assert not s.motion_position_uncertain


def test_queue_rejects_path_traversal_and_idle_enqueue(tmp_path):
    s, lock, ns = fixture(tmp_path)
    route = isolate('main.py', 'queue_next_pattern', ns)
    for name in ('../outside.thr', '/tmp/outside.thr', 'missing.thr', 'foo.txt'):
        with pytest.raises(HTTPException) as e:
            asyncio.run(route(SimpleNamespace(file_name=name)))
        assert e.value.status_code in (400, 404)
    assert len(s.current_playlist) == 1
    s.current_playing_file = None
    with pytest.raises(HTTPException) as e:
        asyncio.run(route(SimpleNamespace(file_name='wave.thr')))
    assert e.value.status_code == 409


def test_queue_rejects_unverified_and_full(tmp_path):
    s, lock, ns = fixture(tmp_path)
    route = isolate('main.py', 'queue_next_pattern', ns)
    s.position_reference_verified = False
    with pytest.raises(HTTPException) as e:
        asyncio.run(route(SimpleNamespace(file_name='wave.thr')))
    assert e.value.status_code == 409
    s.position_reference_verified = True
    s.current_playlist += ['./patterns/star.thr'] * 12
    with pytest.raises(HTTPException) as e:
        asyncio.run(route(SimpleNamespace(file_name='wave.thr')))
    assert e.value.status_code == 409


def test_queue_remove_only_future_item(tmp_path):
    s, lock, ns = fixture(tmp_path)
    s.current_playlist.append('./patterns/wave.thr')
    route = isolate('main.py', 'remove_next_pattern', ns)
    with pytest.raises(HTTPException):
        asyncio.run(route(SimpleNamespace(index=0)))
    result = asyncio.run(route(SimpleNamespace(index=1)))
    assert result['success'] is True
    assert result['removed'] == 'wave.thr'
    assert len(s.current_playlist) == 1


def test_executor_previews_only_after_first_point_idle_and_blocks_next_after_failure():
    p = (ROOT / 'modules/core/pattern_manager.py').read_text()
    assert "entry_confirmed = await _await_confirmed_endpoint(expected_entry, context='pattern entry')" in p
    assert 'async def _await_confirmed_endpoint' in p
    assert "expected_finish, context='pattern finish'" in p
    assert 'completed = await run_theta_rho_file(' in p
    assert 'if not completed:' in p
    assert "logger.error('ORYN halted sequence after an unverified pattern" in p
    js = (ROOT / 'static/dist/oryn-v2-live.js').read_text()
    assert 'data-action="next-add"' in js
    assert 'data-action="next-remove"' in js
    assert 'const nextPreviewPending=new Set()' in js
    assert any(v in js for v in ('CP2N-POSITION-QUEUE-20261112','CP2O-HOME-ACK-SAFETY-20261112'))
    assert 'function home()' in js and 'nextUpPanel()' in js
    assert any(v in (ROOT / 'static/dist/index.html').read_text() for v in ('CP2N-POSITION-QUEUE-20261112','CP2O-HOME-ACK-SAFETY-20261112'))


def test_transient_grbl_idle_does_not_allow_premature_start():
    # First Idle reply still carries the OLD coordinate; two new, agreeing
    # observations are required before the next pattern may be dispatched.
    s=SimpleNamespace(machine_x=0., machine_y=0., position_reference_verified=True,
                      motion_position_uncertain=False, stop_requested=False,
                      conn=SimpleNamespace(is_connected=lambda: True), last_position_check='not checked')
    class Controller:
        calls=0
        async def check_idle_async(self, timeout=8):
            self.calls+=1
            if self.calls==2: s.machine_x=7.;s.machine_y=9.
            return True
    check=Controller()
    fn=isolate('modules/core/pattern_manager.py','_confirm_controller_endpoint',
               {'state':s,'logger':logging.getLogger('cp2n-test')})
    run=isolate('modules/core/pattern_manager.py','_await_confirmed_endpoint',
                {'state':s, 'connection_manager':check,'_confirm_controller_endpoint':fn,
                 'asyncio':asyncio,'logger':logging.getLogger('cp2n-test')})
    assert asyncio.run(run((7.,9.),context='pattern entry',timeout=4.)) is True
    assert check.calls>=3
    assert s.position_reference_verified and not s.motion_position_uncertain


def test_connection_loss_blocks_controller_endpoint_and_next_pattern():
    s=SimpleNamespace(machine_x=7., machine_y=9., position_reference_verified=False,
                      motion_position_uncertain=False, stop_requested=False,
                      conn=SimpleNamespace(is_connected=lambda: False))
    class Controller:
        async def check_idle_async(self, timeout=8):
            raise AssertionError('Must not poll a disconnected controller')
    fn=isolate('modules/core/pattern_manager.py','_confirm_controller_endpoint',
               {'state':s,'logger':logging.getLogger('cp2n-test')})
    run=isolate('modules/core/pattern_manager.py','_await_confirmed_endpoint',
                {'state':s,'connection_manager':Controller(),'_confirm_controller_endpoint':fn,
                 'asyncio':asyncio,'logger':logging.getLogger('cp2n-test')})
    assert asyncio.run(run((7.,9.),context='pattern finish',timeout=1.)) is False
    assert s.motion_position_uncertain and s.stop_requested
