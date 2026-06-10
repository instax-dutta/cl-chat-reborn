from core.dm import encode_dm, decode_dm


class TestDM:
    def test_roundtrip(self):
        encoded = encode_dm("Bob", "hello")
        is_dm, target, body = decode_dm(encoded)
        assert is_dm is True
        assert target == "Bob"
        assert body == "hello"

    def test_non_dm_passthrough(self):
        is_dm, target, body = decode_dm("normal message")
        assert is_dm is False
        assert body == "normal message"

    def test_dm_wrong_target_discarded(self):
        encoded = encode_dm("Bob", "secret")
        is_dm, target, body = decode_dm(encoded)
        assert target == "Bob"
        assert target != "Alice"

    def test_empty_body(self):
        encoded = encode_dm("Bob", "")
        is_dm, target, body = decode_dm(encoded)
        assert is_dm is True
        assert body == ""
