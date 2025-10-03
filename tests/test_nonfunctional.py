import random
import time
import pytest
from hackernews.client import HackerNewsClient


@pytest.fixture(scope="session")
def client():
    return HackerNewsClient(retries=2, backoff=0.3, timeout=6.0)


# -------- Non-functional: robustness/reliability/sanity --------

@pytest.mark.nonfunctional
@pytest.mark.robustness
def test_deleted_or_dead_items_flags_present_when_set(client):
    scanned = 0
    for sid in client.top_stories()[:80]:
        it = client.item(sid)
        scanned += 1
        if it and (it.get("deleted") or it.get("dead")):
            assert isinstance(it.get("deleted", False), bool)
            assert isinstance(it.get("dead", False), bool)
            break
    assert scanned > 0


@pytest.mark.nonfunctional
@pytest.mark.robustness
def test_deep_nesting_traverse_first_levels(client):
    for sid in client.top_stories()[:30]:
        story = client.item(sid)
        if not story or not story.get("kids"):
            continue
        level1 = [client.item(k) for k in story["kids"][:10]]
        level1 = [c for c in level1 if c and not c.get("deleted") and not c.get("dead")]
        level2_ids = []
        for c in level1:
            kids = c.get("kids") or []
            level2_ids.extend(kids[:5])
        if level2_ids:
            level2 = [client.item(k) for k in level2_ids[:10]]
            now = int(time.time()) + 300
            for it in level2:
                if it:
                    assert isinstance(it.get("time"), int) and it["time"] <= now
            return
    pytest.skip("No nested threads found within sample")


@pytest.mark.nonfunctional
@pytest.mark.robustness
@pytest.mark.negative
def test_guard_non_json_path(client, monkeypatch):
    original = client.http.get

    def fake_get(url, **kwargs):
        class R:
            status_code = 200

            def raise_for_status(self): pass

            def json(self): raise ValueError("not json")

        return R()

    monkeypatch.setattr(client.http, "get", fake_get)
    assert client.item(123) is None
    monkeypatch.setattr(client.http, "get", original)


@pytest.mark.nonfunctional
@pytest.mark.robustness
@pytest.mark.positive
@pytest.mark.smoke
def test_smoke_random_property_sampling(client):
    ids = client.top_stories()
    sample = random.sample(ids[:50], k=min(5, len(ids[:50])))
    now = int(time.time()) + 300
    for sid in sample:
        it = client.item(sid)
        if it:
            assert isinstance(it.get("id"), int)
            assert isinstance(it.get("time"), int) and 0 < it["time"] <= now


# Note: Performance classification is implemented via Locust under perf/.
# We expose a marker here so suites can be filtered, but pytest does not run perf itself.
@pytest.mark.nonfunctional
@pytest.mark.performance
def test_performance_suite_is_locust_based():
    """Documentation placeholder so 'pytest -m performance' yields context.
    Actual performance workload is defined in perf/locustfile.py and gated by perf/check_thresholds.py in CI.
    """
    assert True
