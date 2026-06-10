from core.seen_ids import SeenIdCache


class TestSeenIdCache:
    def test_new_id_returns_false(self) -> None:
        cache = SeenIdCache(maxsize=100)
        assert cache.seen("msg-1") is False

    def test_seen_id_returns_true(self) -> None:
        cache = SeenIdCache(maxsize=100)
        cache.seen("msg-1")
        assert cache.seen("msg-1") is True

    def test_empty_id_returns_false(self) -> None:
        cache = SeenIdCache(maxsize=100)
        assert cache.seen("") is False
        assert cache.seen(None) is False

    def test_eviction_on_maxsize(self) -> None:
        cache = SeenIdCache(maxsize=3)
        cache.seen("a")
        cache.seen("b")
        cache.seen("c")
        assert cache.seen("a") is True
        cache.seen("d")
        assert cache.seen("a") is False
        assert cache.seen("d") is True

    def test_thread_safety(self) -> None:
        import threading

        cache = SeenIdCache(maxsize=1000)
        errors = []

        def worker(n: int) -> None:
            for i in range(100):
                try:
                    cache.seen(f"{n}-{i}")
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"thread safety failed: {errors}"
