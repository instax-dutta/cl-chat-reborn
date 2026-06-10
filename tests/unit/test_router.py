import threading
from unittest.mock import MagicMock

from core.router import Router
from core.seen_ids import SeenIdCache
from sanitizer import RateLimiter


class TestRouter:
    def test_router_creation(self) -> None:
        r = Router(
            SeenIdCache(), RateLimiter(), {}, threading.Lock(),
            MagicMock(), MagicMock(), "TestUser",
        )
        assert r.own_username == "TestUser"
