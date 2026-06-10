import threading
from unittest.mock import MagicMock

from core.display import Display
from core.connection import PeerConnection


class TestDisplay:
    def test_display_system_with_ui(self) -> None:
        ui = MagicMock()
        d = Display(ui, "TestUser", {}, threading.Lock())
        d.display_system("hello")
        ui.add_system_message.assert_called_once_with("hello")
