from dataclasses import dataclass, field
import threading
import queue


@dataclass
class FingerprintChallenge:
    host: str
    port: int
    fingerprint: str
    display_name: str
    result_event: threading.Event = field(default_factory=threading.Event)
    accepted: bool = False


challenge_queue: queue.SimpleQueue = queue.SimpleQueue()
