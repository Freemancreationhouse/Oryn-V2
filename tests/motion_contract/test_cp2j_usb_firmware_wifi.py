"""CP2J read-only/offline regressions. No serial devices or network touched."""
from pathlib import Path
import ast
import logging
import re
import time
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]


def selected_function(rel, name, injected):
    path = ROOT / rel
    tree = ast.parse(path.read_text())
    node = next(item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name)
    namespace = {'__builtins__': __builtins__}
    namespace.update(injected)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), 'exec'), namespace)
    return namespace[name]


def test_usb_connect_does_not_claim_home_or_reset():
    state = SimpleNamespace(last_homing_success=True, machine_x=0, machine_y=0,
                            position_reference_verified=True, is_homed=True,
                            conn=SimpleNamespace(close=Mock()))
    fail_if_motion = Mock(side_effect=AssertionError('No reset/motion allowed on connect'))
    fn = selected_function('modules/connection/connection_manager.py', 'device_init', {
        'state': state, 'logger': logging.getLogger('test'),
        'get_machine_steps': Mock(return_value=True),
        'get_machine_position': Mock(return_value=(0.0, 0.0)),
        'perform_soft_reset_sync': fail_if_motion,
        'reset_work_coordinates': fail_if_motion,
        'home': fail_if_motion,
    })
    assert fn() is True
    assert state.last_homing_success is None
    assert state.position_reference_verified is False
    assert state.is_homed is False
    assert state.controller_reported_mpos == (0.0, 0.0)
    assert state.machine_x == 0 and state.machine_y == 0
    fail_if_motion.assert_not_called()


def test_usb_connect_preserves_mismatched_saved_position_without_homing():
    state = SimpleNamespace(last_homing_success=True, machine_x=2.5, machine_y=1.4,
                            position_reference_verified=True, is_homed=True,
                            conn=SimpleNamespace(close=Mock()))
    fn = selected_function('modules/connection/connection_manager.py', 'device_init', {
        'state': state, 'logger': logging.getLogger('test'),
        'get_machine_steps': Mock(return_value=True),
        'get_machine_position': Mock(return_value=(0.0, 0.0)),
    })
    assert fn() is True
    assert (state.machine_x, state.machine_y) == (2.5, 1.4)
    assert state.position_reference_verified is False


class FirmwareSerial:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []
        self.active = []
    def is_connected(self):
        return True
    def in_waiting(self):
        return len(self.active)
    def readline(self):
        return self.active.pop(0)
    def send(self, command):
        self.sent.append(command)
        if command == '$I\n':
            self.active.extend(self.replies)


def firmware_probe(responses):
    conn = FirmwareSerial(responses)
    state = SimpleNamespace(conn=conn)
    fn = selected_function('modules/connection/connection_manager.py','_detect_firmware', {
        'state':state, 'time':SimpleNamespace(time=time.monotonic, sleep=lambda *_:None),
        're':re, 'logger':logging.getLogger('test')})
    result=fn()
    assert conn.sent == ['$I\n']
    return result


def test_grbl_11_identified_by_ver_response():
    assert firmware_probe(['[VER:1.1h.20190825:]', '[OPT:V,15,128]', 'ok']) == ('grbl', '1.1h.20190825')


def test_grbl_banner_identified():
    assert firmware_probe(["Grbl 1.1h ['$' for help]"]) == ('grbl', '1.1h')


def test_unknown_firmware_not_guessed():
    assert firmware_probe(['ok']) == ('unknown', None)


def test_saving_existing_wifi_never_deletes_active_profile():
    calls=[]
    fn=selected_function('modules/wifi/manager.py','save_network', {
        'IS_WINDOWS':False,
        'get_saved_connections':lambda:[{'name':'HomeWifi','ssid':'HomeWifi'}],
        'run_nmcli_check':lambda *a, **kw: calls.append(a),
        'logger':logging.getLogger('test'),
        'subprocess':SimpleNamespace(TimeoutExpired=TimeoutError),
    })
    assert fn('HomeWifi','')['success'] is True
    assert fn('HomeWifi','different-password')['success'] is False
    assert calls == []


def test_wifi_status_reports_hotspot_configured_without_switching():
    calls=[]
    fn=selected_function('modules/wifi/manager.py','get_wifi_status', {
        'IS_WINDOWS':False, 'get_wifi_mode':lambda:'client',
        'get_current_ssid':lambda:'HomeWifi','get_current_ip':lambda:'192.168.0.224',
        'get_hostname':lambda:'oryn','run_nmcli_check':lambda *a,**k:(calls.append(a) or SimpleNamespace(returncode=0)),
        'HOTSPOT_CON_NAME':'ORYNMotion-Hotspot',
        '_run':lambda *a,**k:SimpleNamespace(returncode=0),
    })
    data=fn()
    assert data['mode']=='client' and data['hotspot_configured'] is True and data['hotspot_recovery_enabled'] is True
    assert calls == [('con','show','ORYNMotion-Hotspot')]


def test_approved_v2_native_wifi_visible_in_system_without_legacy_iframe():
    js=(ROOT/'static/dist/oryn-v2-live.js').read_text()
    assert 'function wifiPanel()' in js
    assert '/api/wifi/networks' in js and '/api/wifi/connect' in js
    assert 'Wi-Fi & ORYN hotspot' in js
    assert 'iframe' not in js.lower()
    assert 'ORYN V2 · CP2J' in js
    assert 'ORIGINAL DUNE' not in js.upper()
