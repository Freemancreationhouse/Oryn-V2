"""Best-effort read-only discovery of classic Magic Home/LEDnet lamps on LAN."""
import socket
import time


def main():
    found = {}
    print('ORYN Magic Home LAN discovery — no changes to lights or GRBL')
    print('First connect the controller and Windows PC to the same Wi-Fi/router.')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', 0))
        sock.settimeout(0.5)
        for _ in range(2):
            try:
                sock.sendto(b'HF-A11ASSISTHREAD', ('255.255.255.255', 48899))
            except OSError as exc:
                print('Broadcast blocked:', exc)
                break
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    data, address = sock.recvfrom(1024)
                    if address[0] not in found:
                        found[address[0]] = data[:120].decode(errors='replace').strip()
                except socket.timeout:
                    pass
    if found:
        print('\nPossible LED controllers (verify in Magic Home Pro app):')
        for host, info in sorted(found.items()):
            print(f'  {host}: {info}')
    else:
        print('\nNo legacy discovery replies found. This does not prove the device is offline.')
        print('Find the controller IPv4 address in your router DHCP/device list instead.')
        print('Some newer controller firmwares do not answer this discovery message.')


if __name__ == '__main__':
    main()
