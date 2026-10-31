"""No-hardware Magic Home TCP 5577 regression tests."""
import socketserver
import threading
import time
import unittest
from unittest.mock import patch
from modules.led.magic_home_controller import MagicHomeController
from modules.led.led_interface import LEDInterface


class _FakeMagic(socketserver.BaseRequestHandler):
    packets = []
    power = True
    rgb = (20, 40, 60)

    def handle(self):
        packet = self.request.recv(64)
        _FakeMagic.packets.append(packet)
        if packet == bytes.fromhex('81 8a 8b 96'):
            self.request.sendall(bytes([0x81, 0x33, 0x23 if _FakeMagic.power else 0x24, 0x61, 0x23, 7, *_FakeMagic.rgb, 0, 8, 0, 0xf0, 0x58]))
        if packet[:2] == bytes.fromhex('71 23'):
            _FakeMagic.power = True
        elif packet[:2] == bytes.fromhex('71 24'):
            _FakeMagic.power = False
        elif packet[:1] == bytes([0x31]):
            _FakeMagic.rgb = tuple(packet[1:4])


class TestMagicHome(unittest.TestCase):
    def setUp(self):
        _FakeMagic.packets = []
        _FakeMagic.power = True
        _FakeMagic.rgb = (20, 40, 60)
        self.server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), _FakeMagic)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.controller = MagicHomeController('127.0.0.1', self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def test_private_ipv4_only(self):
        for invalid in ('8.8.8.8', 'localhost', 'example.org', '224.0.0.1', ''):
            with self.assertRaises(ValueError):
                MagicHomeController(invalid)

    def wait_packet(self, expected=None):
        end = time.monotonic() + 1
        while (expected not in _FakeMagic.packets if expected is not None else not _FakeMagic.packets) and time.monotonic() < end:
            time.sleep(0.002)
        self.assertTrue(_FakeMagic.packets, 'Mock device did not receive a packet')
        if expected is not None:
            self.assertIn(expected, _FakeMagic.packets)

    def test_protocol_status_and_on_off(self):
        status = self.controller.check_status()
        self.assertTrue(status['connected'])
        self.assertTrue(status['is_on'])
        self.assertEqual(status['color'], '#14283c')
        self.assertTrue(self.controller.set_power(0)['connected'])
        self.wait_packet(bytes.fromhex('71 24 0f a4'))
        self.assertFalse(self.controller.check_status()['is_on'])
        self.assertTrue(self.controller.set_power(1)['connected'])
        self.wait_packet(bytes.fromhex('71 23 0f a3'))
        self.assertTrue(self.controller.check_status()['is_on'])

    def test_rgb_and_brightness_checksum(self):
        result = self.controller.set_color(255, 128, 0, brightness=50)
        self.assertTrue(result['connected'])
        self.wait_packet()
        p = _FakeMagic.packets[-1]
        self.assertEqual(p[:-1], bytes([0x31, 128, 64, 0, 0, 0xf0, 0x0f]))
        self.assertEqual(p[-1], sum(p[:-1]) % 256)
        self.assertEqual(_FakeMagic.rgb, (128, 64, 0))
        self.assertFalse(self.controller.set_color(-1, 0, 0)['connected'])
        self.assertFalse(self.controller.set_color(100, 0, 0, brightness=101)['connected'])

    def test_unavailable_device_is_failure_not_success(self):
        with patch('modules.led.magic_home_controller.socket.create_connection', side_effect=ConnectionError('offline')):
            self.assertFalse(self.controller.check_status()['connected'])
            self.assertFalse(self.controller.set_power(1)['connected'])

    def test_interface_keeps_separate_backend(self):
        wled = LEDInterface('wled', '192.168.1.1')
        magic = LEDInterface('magic_home', '127.0.0.1')
        self.assertEqual(wled.provider, 'wled')
        self.assertEqual(magic.provider, 'magic_home')
        self.assertNotEqual(type(wled.get_controller()), type(magic.get_controller()))


if __name__ == '__main__':
    unittest.main()
