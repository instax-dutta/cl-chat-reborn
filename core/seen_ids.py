from collections import deque
import threading


class SeenIdCache:
    def __init__(self, maxsize: int = 10_000):
        self._dq: deque = deque(maxlen=maxsize)
        self._set: set = set()
        self._lock = threading.Lock()

    def seen(self, msg_id: str) -> bool:
        """Returns True if already seen; registers and returns False if new."""
        if not msg_id:
            return False
        with self._lock:
            if msg_id in self._set:
                return True
            if len(self._dq) >= self._dq.maxlen:
                self._set.discard(self._dq[0])
            self._dq.append(msg_id)
            self._set.add(msg_id)
            return False
