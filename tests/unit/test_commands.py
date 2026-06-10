import threading
from unittest.mock import MagicMock

from core.commands import Commander


class TestCommander:
    def test_unknown_command_does_not_crash(self) -> None:
        display = MagicMock()
        c = Commander(
            "TestUser", {}, threading.Lock(), display,
            MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        )
        c.handle_command("/nonexistent")
        display.display_system.assert_called_once()
