"""Offline regression guarding CP2Q against self-confirming position checks."""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]

def load_endpoint(state):
    source=ROOT/'modules/core/pattern_manager.py'
    tree=ast.parse(source.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_confirm_controller_endpoint')
    ns={'state':state,'logger':logging.getLogger('oryn-cp2q')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),ns)
    return ns['_confirm_controller_endpoint']

def test_commanded_pose_cannot_self_confirm():
    state=SimpleNamespace(machine_x=77.683,machine_y=-14.,position_reference_verified=True,
                          motion_position_uncertain=False,stop_requested=False)
    validate=load_endpoint(state)
    assert not validate((77.683,-14.),context='test')
    assert state.motion_position_uncertain and not state.position_reference_verified

def test_independent_controller_mismatch_stops():
    state=SimpleNamespace(machine_x=77.683,machine_y=-14.,position_reference_verified=True,
                          motion_position_uncertain=False,stop_requested=False)
    validate=load_endpoint(state)
    assert not validate((77.683,-14.), observed_xy=(77.683,-13.2),context='test')
    assert state.stop_requested

def test_independent_controller_within_tolerance_accepted():
    state=SimpleNamespace(machine_x=77.683,machine_y=-14.,position_reference_verified=True,
                          motion_position_uncertain=False,stop_requested=False)
    validate=load_endpoint(state)
    assert validate((77.683,-14.),observed_xy=(77.684,-14.001),context='test')
    assert not state.motion_position_uncertain
