"""CP2R source tests: calibration jog uses pattern-equivalent coupling and one XY jog."""
import ast
import asyncio
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from modules.core.kinematics_contract import dune_coupled_delta

ROOT=Path(__file__).resolve().parents[2]

def route(name,ns):
    tree=ast.parse((ROOT/'main.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
    node.decorator_list=[]
    scope=dict(ns)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'main.py'),'exec'),scope)
    return scope[name]

class Motor:
    def __init__(self): self.calls=[];self.idle=True;self.ack=True
    async def send_grbl_coordinates(self,*a,**kw):self.calls.append((a,kw));return self.ack
    async def check_idle_async(self,**kw):return self.idle
    async def update_machine_position(self):return None

def fixture():
    s=SimpleNamespace(conn=SimpleNamespace(is_connected=lambda:True),rotation_calibration_active=True,
        rotation_calibration_start_x=0.,rotation_calibration_current_units=0.,machine_x=0.,
        motion_position_uncertain=False,theta_calibrated=True,theta_revolution_units=78.,
        rho_calibrated=True,rho_travel_units=51.504,rho_direction=1.,
        x_steps_per_mm=205.,y_steps_per_mm=143.504,gear_ratio=10.,table_type='kinetiq_motion',
        table_type_override=None)
    motor=Motor()
    return s,motor,route('jog_rotation_calibration',dict(state=s,connection_manager=motor,logger=logging.getLogger('test'),
        HTTPException=HTTPException,os=os,RotationCalibrationJogRequest=SimpleNamespace))

@pytest.mark.parametrize('delta', [0.5,-0.5,5.,-5.,25.])
def test_coupling_from_pattern_contract_and_x_only_counter(delta):
    s,m,jog=fixture()
    result=asyncio.run(jog(SimpleNamespace(units=delta,speed=80.)))
    (args,kw),=m.calls
    assert args[0]==delta
    assert args[1]==pytest.approx(delta*205/(10*143.504),abs=1e-12)
    assert kw['jog_axis']=='xy' and kw['calibration_single_attempt'] is True
    assert result['current_units']==pytest.approx(delta)
    assert s.theta_revolution_units==78. and s.rho_travel_units==51.504 and s.gear_ratio==10.


def test_mechanical_winding_reverse_for_mini():
    s,m,jog=fixture();s.table_type='kinetiq_motion_mini'
    asyncio.run(jog(SimpleNamespace(units=2.,speed=80.)))
    assert m.calls[0][0][1] == pytest.approx(-2*205/(10*143.504))


def test_unsafe_jog_rejected_without_sending():
    for value in (0,26,float('nan'),float('inf')):
        s,m,jog=fixture()
        with pytest.raises(HTTPException): asyncio.run(jog(SimpleNamespace(units=value,speed=80.)))
        assert not m.calls


def test_unsafe_position_rejected_without_sending():
    s,m,jog=fixture();s.motion_position_uncertain=True
    with pytest.raises(HTTPException) as e: asyncio.run(jog(SimpleNamespace(units=1.,speed=80.)))
    assert e.value.status_code==409 and not m.calls


def test_missing_ack_does_not_accumulate_and_blocks_session():
    s,m,jog=fixture();m.ack=False
    with pytest.raises(HTTPException): asyncio.run(jog(SimpleNamespace(units=1.,speed=80.)))
    assert s.rotation_calibration_current_units==0 and s.motion_position_uncertain and not s.rotation_calibration_active


def test_grbl_coordinate_sender_has_atomic_xy_jog():
    source=(ROOT/'modules/connection/connection_manager.py').read_text()
    tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='send_grbl_coordinates')
    assert any(isinstance(n,ast.Compare) and any(isinstance(c,ast.Constant) and c.value=='xy' for c in n.comparators) for n in ast.walk(node))
    assert '"$J=G91 G21 X{x:.3f} Y{y:.3f} F{speed}"' in source
