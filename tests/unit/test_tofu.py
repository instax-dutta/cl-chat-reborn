from core.tofu import TofuStore


class TestTofuStore:
    def test_known_hosts_path_ends_correctly(self) -> None:
        t = TofuStore(encryption_enabled=True)
        path = t.known_hosts_path()
        assert path.endswith('.clchat/known_hosts.json')
