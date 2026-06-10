from core.connection import ReconnectState


class TestReconnectState:
    def test_backoff_schedule(self):
        state = ReconnectState(host="127.0.0.1", port=9000, base_delay=2.0)
        assert state.next_delay() == 2.0
        state.attempt = 1
        assert state.next_delay() == 4.0
        state.attempt = 2
        assert state.next_delay() == 8.0
        state.attempt = 3
        assert state.next_delay() == 16.0
        state.attempt = 4
        assert state.next_delay() == 32.0
        state.attempt = 5
        assert state.next_delay() == 32.0  # capped

    def test_max_attempts_default(self):
        state = ReconnectState(host="127.0.0.1", port=9000)
        assert state.max_attempts == 5

    def test_next_delay_capped(self):
        state = ReconnectState(host="127.0.0.1", port=9000, base_delay=2.0)
        for i in range(10):
            state.attempt = i
            delay = state.next_delay()
            assert delay <= 32.0
