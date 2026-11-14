from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from marketplace import cache


@pytest.fixture(autouse=True)
def empty_cache():
    cache._entries.clear()
    yield
    cache._entries.clear()


def test_reuse_filter_isolation_expiry_and_copy(monkeypatch):
    clock = [0]
    monkeypatch.setattr(cache, "monotonic", lambda: clock[0])
    calls = []
    @cache.cached
    def query(params):
        calls.append(params)
        return {"rows": [len(calls)]}
    first = query({"state": "SP", "year": 2017})
    first["rows"].append(99)
    assert query({"year": 2017, "state": "SP"}) == {"rows": [1]}
    assert query({"state": "RJ", "year": 2017}) == {"rows": [2]}
    clock[0] = 301
    assert query({"state": "SP", "year": 2017}) == {"rows": [3]}


def test_failures_are_retried_and_cache_is_bounded(monkeypatch):
    calls = []
    monkeypatch.setattr(cache, "MAX_ENTRIES", 2)
    @cache.cached
    def query(value):
        calls.append(value)
        if len(calls) == 1:
            raise ValueError("temporary failure")
        return value
    with pytest.raises(ValueError):
        query(1)
    assert query(1) == 1
    query(2)
    query(3)
    assert len(cache._entries) == 2
    query(1)
    assert calls == [1, 1, 2, 3, 1]


def test_simultaneous_requests_share_work():
    entered, release = Event(), Event()
    calls = []
    @cache.cached
    def query():
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return {"value": 42}
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(query)
        assert entered.wait(5)
        second = pool.submit(query)
        release.set()
        assert first.result() == second.result() == {"value": 42}
    assert len(calls) == 1
