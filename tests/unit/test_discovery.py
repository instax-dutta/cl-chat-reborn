class TestDiscoveryImports:
    def test_discovery_module_imports(self):
        from core.discovery import LocalDiscovery, _get_local_ip, SERVICE_TYPE
        assert SERVICE_TYPE == "_clchat._tcp.local."
        ip = _get_local_ip()
        assert isinstance(ip, str)
