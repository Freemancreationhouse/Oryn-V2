"""CP2O regression: premature HOME Idle and serial ACK ownership, no motors."""
import ast
import logging
import threading
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'modules/connection/connection_manager.py'


def isolated(name, ns):
    tree=ast.parse(SOURCE.read_text())
    node=next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name==name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])), str(SOURCE), 'exec'), ns)
    return ns[name]


class Clock:
    def __init__(self): self.t=0.0
    def monotonic(self): return self.t
    def sleep(self, seconds): self.t += seconds


class FakeConn:
    def __init__(self, clock, ack='ok'):
        self.clock=clock
        self.ack=ack
        self.sent=[]
        self.lock=threading.RLock()
        self.jogged=False
        self.reply_ready=False
    def send(self, text):
        self.sent.append(text)
        if text.startswith('$J='):
            self.jogged=True
            self.reply_ready=True
    def readline(self):
        if self.reply_ready:
            self.reply_ready=False
            return self.ack
        return ''
    def is_connected(self): return True


def scenario(kind, ack='ok'):
    clock=Clock()
    conn=FakeConn(clock, ack)
    s=SimpleNamespace(conn=conn,homing_error=None,last_homing_success=None,
                      position_reference_verified=False,motion_position_uncertain=False,
                      stop_requested=False)
    def status(timeout=3):
        if not conn.jogged:
            return '<Idle|MPos:0.000,0.000,0.000|FS:0,0>'
        if kind=='premature_idle':
            return '<Idle|MPos:0.000,-3.965,0.000|FS:0,0>'
        if kind=='alarm':
            return '<Alarm|MPos:0.000,-3.965,0.000|FS:0,0>'
        if clock.t < 12.0:
            y=-51.504 * min(1., clock.t/12.0)
            return f'<Jog|MPos:0.000,{y:.3f},0.000|FS:0,0>'
        return '<Idle|MPos:0.000,-51.504,0.000|FS:0,0>'
    def position(response):
        import re
        m=re.search(r'MPos:([^|]+)',response)
        if not m:return None
        return tuple(float(v) for v in m.group(1).split(',')[:2])
    ns={'state':s, 'time':clock, 'get_status_response':status,
        'parse_machine_position':position, 'logger':logging.getLogger('oryn-test')}
    return isolated('_send_crash_home_jog_once',ns),s,conn,clock


def test_reported_1_second_home_is_rejected_not_marked_center():
    f,s,c,t=scenario('premature_idle')
    assert f(51.504,257.52,1.0) is False
    assert s.motion_position_uncertain and not s.position_reference_verified
    assert s.homing_error=='home_travel_incomplete'
    assert sum(cmd.startswith('$J=') for cmd in c.sent)==1
    assert t.t >= 12.0
    assert '!' in c.sent  # feed hold on uncertainty, never repeat


def test_full_travel_and_stable_idle_can_be_reported_as_controller_confirmed():
    f,s,c,t=scenario('normal')
    assert f(51.504,257.52,1.0) is True
    assert sum(cmd.startswith('$J=') for cmd in c.sent)==1
    assert t.t >= 12.0
    assert s.position_reference_verified is False  # operator must confirm physical center


def test_missing_jog_ack_does_not_retry_relative_home():
    f,s,c,t=scenario('normal',ack='')
    assert f(51.504,257.52,1.0) is False
    assert sum(cmd.startswith('$J=') for cmd in c.sent)==1
    assert s.motion_position_uncertain


def test_alarm_during_home_fails_closed():
    f,s,c,t=scenario('alarm')
    assert f(51.504,257.52,1.0) is False
    assert s.motion_position_uncertain


def test_status_transaction_uses_shared_serial_lock():
    clock=Clock()
    class ProbingLock:
        def __init__(self): self.held=False
        def __enter__(self): self.held=True
        def __exit__(self,*args): self.held=False
    lock=ProbingLock()
    class StatusConn:
        def is_connected(self):return True
        def send(self,s):
            assert lock.held
            assert s=='?'
        def readline(self):
            assert lock.held
            return '<Idle|MPos:0.000,0.000,0.000>'
    conn=StatusConn();conn.lock=lock
    ns={'state':SimpleNamespace(conn=conn),'logger':logging.getLogger('oryn-test'),
        'time':clock}
    assert isolated('get_status_response',ns)()=='<Idle|MPos:0.000,0.000,0.000>'
    assert lock.held is False
