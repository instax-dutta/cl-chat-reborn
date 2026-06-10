import socket
from typing import Callable, Optional

from zeroconf import ServiceBrowser, ServiceStateChange, ServiceInfo, Zeroconf


SERVICE_TYPE = "_clchat._tcp.local."


def _get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class LocalDiscovery:
    def __init__(self, username: str, port: int, on_peer_found: Callable[[str, str, int], None]):
        self.zc = Zeroconf()
        self._callback = on_peer_found

        local_ip = _get_local_ip()
        info = ServiceInfo(
            SERVICE_TYPE,
            f"{username}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"u": username},
        )
        self.zc.register_service(info)
        self.browser = ServiceBrowser(self.zc, SERVICE_TYPE, handlers=[self._on_service_state])

    def _on_service_state(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.parsed_addresses() and info.port:
                peer_username = info.properties.get(b"u", b"").decode("utf-8") if info.properties else ""
                if peer_username:
                    peer_ip = info.parsed_addresses()[0]
                    self._callback(peer_username, peer_ip, info.port)

    def close(self):
        self.zc.close()
