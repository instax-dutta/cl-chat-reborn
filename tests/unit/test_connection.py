from core.connection import PeerConnection, recv_line, send_line


class TestPeerConnection:
    def test_peer_connection_repr(self) -> None:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = PeerConnection(s, ('127.0.0.1', 9000))
        assert "Peer" in repr(conn)
        s.close()
