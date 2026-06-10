"""
Input sanitization and rate limiting for CL Chat.
"""

import re
import time
from collections import defaultdict, deque


USERNAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{1,19}$')
MAX_MESSAGE_LENGTH = 4096
MAX_USERNAME_LENGTH = 20
MAX_PEER_COUNT = 50
RATE_LIMIT_WINDOW = 10
RATE_LIMIT_MAX = 30


def check_username(name: str):
    """Validate and sanitize a username. Returns sanitized name or None."""
    if not name or not isinstance(name, str):
        return None
    name = name.strip()
    name = ''.join(c for c in name if c.isprintable() and c not in '\n\r\t')
    if len(name) > MAX_USERNAME_LENGTH:
        name = name[:MAX_USERNAME_LENGTH]
    if not USERNAME_RE.match(name):
        return None
    return name


def clean_message(msg: str):
    """Sanitize a chat message. Returns cleaned string."""
    if not msg or not isinstance(msg, str):
        return ""
    if len(msg) > MAX_MESSAGE_LENGTH:
        msg = msg[:MAX_MESSAGE_LENGTH]
    cleaned = ''.join(c for c in msg if c.isprintable() or c in '\n\t')
    return cleaned.strip()


def validate_peer_count(count: int) -> bool:
    """Check peer count hasn't exceeded maximum."""
    return count < MAX_PEER_COUNT


class RateLimiter:
    """Sliding-window rate limiter per key."""

    def __init__(self, max_events: int = RATE_LIMIT_MAX, window: float = RATE_LIMIT_WINDOW):
        self.max_events = max_events
        self.window = window
        self._buckets: dict = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        times = self._buckets[key]
        cutoff = now - self.window
        while times and times[0] < cutoff:
                times.popleft()
        if len(times) >= self.max_events:
            return False
        times.append(now)
        return True

    def reset(self, key: str):
        self._buckets.pop(key, None)
