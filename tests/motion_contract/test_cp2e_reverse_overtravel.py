"""CP2E regression: fail closed when command completion is uncertain.

Pure simulation only. GRBL 'ok' acknowledges planner acceptance, not observed
physical motion. These tests do not certify motor steps, belts or gear backlash.
"""
import ast
from pathlib import Path
import math
import logging
import types
import contextlib
import pytest
from modules.core.kinematics_contract import dune_coupled_delta

ROOT = Path(__file__).resolve().parents[2]


def load_sender(monkeypatch):
    code = ast.parse((ROOT/'modules/core/pattern_manager.py').read_text(encoding='utf8'))
    klass = next(n for n in code.body if isinstance(n,ast.ClassDef) and n.name=='MotionControlThread')
    method = next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='_send_grbl_coordinates_sync')
    isolated=ast.Module(body=[ast.ClassDef(name='Control',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[])
    ast.fix_missing_locations(isolated)
    clock=types.SimpleNamespace(t=0.0)
    def tick():
        clock.t+=3.2
        return clock.t
    mod={'logger':logging.getLogger('cp2e-test'),'state':None, 'time':types.SimpleNamespace(monotonic=tick)}
    exec(compile(isolated,'cp2e_sender','exec'),mod)
    return mod['Control'],mod


class FakeGRBL:
    def __init__(self,responses,*,stale=False,exception=None):
        self.responses=iter(responses)
        self.sent=[]
        self.stale=stale
        self.exception=exception
        self.lock=contextlib.nullcontext()
    def is_connected(self):return True
    def in_waiting(self):return 1 if self.stale else 0
    def send(self,msg):
        if self.exception and msg!='!':raise self.exception
        self.sent.append(msg)
    def readline(self):return next(self.responses,'')


def sender_fixture(monkeypatch,responses=(),**kwargs):
    Control,mod=load_sender(monkeypatch)
    conn=FakeGRBL(responses,**kwargs)
    state=types.SimpleNamespace(conn=conn,stop_requested=False, motion_position_uncertain=False,last_motion_error=None)
    mod['state']=state
    return Control(),state,conn


def test_legacy_absolute_success_ack_once(monkeypatch):
    control,state,conn=sender_fixture(monkeypatch,['<Run|MPos:1,0,0>','ok'])
    assert control._send_grbl_coordinates_sync(5,0.5,30)
    assert conn.sent == ['G90 G21 G1 X5.00000 Y0.50000 F30.000\n']
    assert state.motion_position_uncertain is False


def test_home_relative_command_sent_once_with_ack(monkeypatch):
    control,state,conn=sender_fixture(monkeypatch,['ok'])
    assert control._send_grbl_coordinates_sync(0,-.2,30,home=True)
    assert conn.sent == ['$J=G91 G21 Y-0.200 F30.000\n']

@pytest.mark.parametrize('response', ['<Idle|MPos:1,2,0>','<Run|MPos:1,2,0>','<Hold|MPos:1,2,0>','[MSG:Connected]',''])
def test_status_or_silence_never_proves_move_accepted(monkeypatch,response):
    control,state,conn=sender_fixture(monkeypatch,[response]*3)
    assert not control._send_grbl_coordinates_sync(0,-.2,30,home=True)
    assert state.motion_position_uncertain
    assert state.stop_requested
    assert conn.sent.count('$J=G91 G21 Y-0.200 F30.000\n')==1
    assert conn.sent[-1]=='!'

@pytest.mark.parametrize('response',['error:2','ALARM:1','alarm:2'])
def test_error_fails_closed_without_replay(monkeypatch,response):
    control,state,conn=sender_fixture(monkeypatch,[response])
    assert not control._send_grbl_coordinates_sync(1,0,30)
    assert state.last_motion_error=='controller_rejected_or_alarm'
    assert len([i for i in conn.sent if i.startswith('G90')])==1
    assert conn.sent[-1]=='!'


def test_stale_reply_blocks_command_before_send(monkeypatch):
    control,state,conn=sender_fixture(monkeypatch,['ok'],stale=True)
    assert not control._send_grbl_coordinates_sync(1,0,30)
    assert not any(i.startswith('G90') for i in conn.sent)
    assert state.last_motion_error=='stale_controller_response'


def test_serial_exception_fails_closed(monkeypatch):
    control,state,conn=sender_fixture(monkeypatch,[],exception=OSError('port disconnected'))
    assert not control._send_grbl_coordinates_sync(1,0,30)
    assert state.motion_position_uncertain
    assert state.last_motion_error=='movement_transport_error'


def test_default_gear_ratio_stays_ten_to_one():
    text=(ROOT/'modules/core/state.py').read_text()
    assert 'self.gear_ratio = 10' in text
    for dx,dr in [(5,.1),(-5,-.1),(15,0),(-15,0)]:
        m=dune_coupled_delta(dx,dr,x_steps=205,y_steps=143.504,gear_ratio=10)
        assert m.coupling==pytest.approx(m.x*205/(10*143.504))


def test_three_forward_one_reverse_mathematically_symmetric():
    cmds=[(5,.762),(5,.762),(5,.762),(-15,-2.286)]
    assert sum(x for x,_ in cmds)==pytest.approx(0)
    assert sum(y for _,y in cmds)==pytest.approx(0)
    # GRBL step discretization may still introduce about a step: this is not
    # a proof of no real overshoot, but confirms no gross software imbalance.
    x_units=205.;y_units=143.504
    y_quantized=sum(round(y*y_units) for _,y in cmds)
    assert abs(y_quantized)<=2
    assert sum(round(x*x_units) for x,_ in cmds)==0


def test_all_clean_files_have_radial_motion_after_twelve_turns():
    clean=list((ROOT/'patterns').glob('clear*.thr'))
    assert len(clean)>=11
    for filename in clean:
        points=[]
        for line in filename.read_text(encoding='utf8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            fields=line.split()
            points.append((float(fields[0]),float(fields[1])))
        assert len(points)>1000
        start=points[0][0]
        later=[r for t,r in points if 12*math.tau<=abs(t-start)<=13*math.tau]
        if later:
            assert max(later)-min(later)>0.001, filename.name

@pytest.mark.parametrize('bad', [[(0,1.005)],[(0,-.01)],[(float('nan'),.3)],[(1,float('inf'))]])
def test_unsafe_coordinates_blocked_without_clamping(bad):
    from modules.core.kinematics_contract import validate_thr_coordinates
    with pytest.raises(ValueError):validate_thr_coordinates(bad)


def test_valid_clean_geometry_accepted():
    from modules.core.kinematics_contract import validate_thr_coordinates
    assert validate_thr_coordinates([(0,1),(math.tau*12,.6),(math.tau*20,0)])


def test_one_known_unsafe_pattern_is_detected_not_silently_altered():
    from modules.core.kinematics_contract import validate_thr_coordinates
    p=ROOT/'patterns/pattern-superellipse.thr'
    rows=[tuple(map(float,s.split()[:2])) for s in p.read_text().splitlines() if s.strip() and not s.startswith('#')]
    with pytest.raises(ValueError,match='rho .* outside'):
        validate_thr_coordinates(rows)
    assert rows[-1][1]==1.005


def test_runtime_executor_calls_validation_before_first_motor_move():
    source=(ROOT/'modules/core/pattern_manager.py').read_text()
    fn=source.index('async def _execute_pattern_internal(')
    first=source[fn:fn+2400]
    assert first.index('validate_thr_coordinates(coordinates)') < first.index('await reset_theta()') if 'await reset_theta()' in first else 'validate_thr_coordinates(coordinates)' in first


def test_calibrated_sender_rejection_marks_position_uncertain():
    source=(ROOT/'modules/core/pattern_manager.py').read_text()
    beg=source.index('def _send_grbl_coupled_delta_sync(')
    end=source.index('def _restore_absolute_mode_sync(',beg)
    method=source[beg:end]
    assert "state.last_motion_error = 'relative_controller_rejected'" in method
    assert "state.last_motion_error = 'relative_transport_error'" in method
