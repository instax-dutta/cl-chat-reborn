import os
import json
from typing import Callable, Optional


class TofuStore:
    def __init__(self, encryption_enabled: bool, display_system_cb: Optional[Callable[[str], None]] = None):
        self.encryption_enabled = encryption_enabled
        self._display_system = display_system_cb or (lambda msg: None)

    @staticmethod
    def known_hosts_path() -> str:
        return os.path.join(os.path.expanduser('~'), '.clchat', 'known_hosts.json')

    def load_known_hosts(self) -> dict:
        path = self.known_hosts_path()
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_fingerprint(self, host: str, port: int, fingerprint: str):
        path = self.known_hosts_path()
        hosts = self.load_known_hosts()
        hosts[f"{host}:{port}"] = fingerprint
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(hosts, f, indent=2)
        os.replace(tmp, path)

    def verify_fingerprint(self, host: str, port: int, fingerprint: str, display_name: str) -> bool:
        """TOFU verification. Returns True if fingerprint is accepted."""
        if not fingerprint or not self.encryption_enabled:
            return True

        hosts = self.load_known_hosts()
        key = f"{host}:{port}"

        if key in hosts:
            stored = hosts[key]
            if stored == fingerprint:
                return True

            self._display_system(
                f"\u26a0\ufe0f  SECURITY WARNING: {display_name} ({host}:{port}) fingerprint mismatch!\n"
                f"    Previous: {stored[:20]}...\n"
                f"    Current:  {fingerprint[:20]}...\n"
                f"    Full: {fingerprint}\n"
                f"    Possible MITM attack or peer re-installed with new key."
            )
        else:
            self._display_system(
                f"First connection to {display_name} ({host}:{port})\n"
                f"  Fingerprint: {fingerprint}\n"
                f"  Verify this fingerprint with the peer out-of-band."
            )

        from core.fingerprint_challenge import challenge_queue, FingerprintChallenge
        challenge = FingerprintChallenge(
            host=host, port=port,
            fingerprint=fingerprint, display_name=display_name,
        )
        challenge_queue.put(challenge)
        if not challenge.result_event.wait(timeout=30.0):
            self._display_system("Fingerprint verification timed out \u2014 connection rejected.")
            return False

        if challenge.accepted:
            self.save_fingerprint(host, port, fingerprint)
            return True
        return False
