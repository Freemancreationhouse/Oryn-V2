"""Local, legacy Magic Home RGB Wi-Fi controller (TCP 5577) integration.

Only sends legacy RGB strip protocol to an explicitly configured private-LAN IP.
Newer Magic Home variants may use another protocol; never claim support until
real hardware confirms it. Does not control GRBL, homing, or motion.
"""
import ipaddress
import logging
import socket
from threading import RLock

logger = logging.getLogger(__name__)


class MagicHomeController:
    def __init__(self, ip_address: str, port: int = 5577):
        address = ipaddress.ip_address(str(ip_address).strip())
        if address.version != 4 or not address.is_private or address.is_multicast or address.is_unspecified:
            raise ValueError("Magic Home requires a local private IPv4 address (for example 192.168.1.50)")
        self.ip_address = str(address)
        self.port = port
        self._lock = RLock()
        self._last_color = (255, 180, 110)
        self._brightness = 70  # percent, until first confirmed state
        self._on = None

    def _io(self, payload: bytes, response: bool = False) -> bytes:
        with self._lock:
            with socket.create_connection((self.ip_address, self.port), timeout=1.7) as sock:
                sock.settimeout(1.7)
                sock.sendall(payload)
                if not response:
                    return b""
                result = sock.recv(64)
                if len(result) < 10 or result[0] != 0x81:
                    raise ValueError("Device did not provide a legacy Magic Home RGB status response")
                return result

    @staticmethod
    def _checksum(data: bytes) -> bytes:
        return data + bytes([sum(data) & 0xFF])

    def check_status(self) -> dict:
        try:
            response = self._io(bytes.fromhex('81 8a 8b 96'), response=True)
            power = response[2] == 0x23
            if response[2] not in (0x23, 0x24):
                raise ValueError("Unsupported Magic Home status packet")
            rgb = tuple(response[6:9])
            with self._lock:
                self._on = power
                if len(rgb) == 3 and max(rgb) > 0:
                    self._brightness = round(100 * max(rgb) / 255)
                    self._last_color = tuple(round(channel * 255 / max(rgb)) for channel in rgb)
            return {"connected": True, "is_on": power, "power_on": power,
                    "brightness": self._brightness, "color": '#%02x%02x%02x' % rgb,
                    "message": "Magic Home connected (local Wi-Fi)"}
        except (OSError, ValueError, IndexError) as exc:
            return {"connected": False, "message": str(exc), "error": str(exc)}

    def set_power(self, state: int) -> dict:
        if state not in (0, 1, 2):
            return {"connected": False, "error": "Power state must be 0, 1, or 2"}
        if state == 2:
            status = self.check_status()
            if not status["connected"]:
                return status
            state = 0 if status["is_on"] else 1
        try:
            self._io(self._checksum(bytes([0x71, 0x23 if state else 0x24, 0x0F])))
            with self._lock:
                self._on = bool(state)
            return {"connected": True, "is_on": bool(state), "power_on": bool(state),
                    "message": "Magic Home power command sent (verify on LEDs)"}
        except OSError as exc:
            return {"connected": False, "message": str(exc), "error": str(exc)}

    def set_color(self, r: int, g: int, b: int, brightness: int = None) -> dict:
        if any(type(c) is not int or not 0 <= c <= 255 for c in (r, g, b)):
            return {"connected": False, "error": "RGB values must be integers from 0 to 255"}
        if brightness is not None and (type(brightness) is not int or not 0 <= brightness <= 100):
            return {"connected": False, "error": "Brightness must be an integer from 0 to 100"}
        level = self._brightness if brightness is None else brightness
        try:
            scaled = [round(c * level / 100) for c in (r, g, b)]
            self._io(self._checksum(bytes([0x31, *scaled, 0x00, 0xF0, 0x0F])))
            with self._lock:
                self._last_color = (r, g, b)
                self._brightness = level
            return {"connected": True, "color": '#%02x%02x%02x' % tuple(scaled),
                    "brightness": level, "message": "Magic Home RGB command sent (verify on LEDs)"}
        except OSError as exc:
            return {"connected": False, "error": str(exc), "message": str(exc)}

    def set_brightness(self, brightness: int) -> dict:
        return self.set_color(*self._last_color, brightness=brightness)


def effect_loading(controller):
    return controller.set_color(255, 156, 0, brightness=30).get('connected', False)


def effect_idle(controller, effect_name=None):
    return controller.set_color(255, 180, 110, brightness=25).get('connected', False)


def effect_connected(controller):
    return controller.check_status().get('connected', False)


def effect_playing(controller, effect_name=None):
    return controller.set_color(255, 180, 110, brightness=65).get('connected', False)
