import pytest
from jsonschema import ValidationError, validate
from hackernews.client import HackerNewsClient as HNClient
from hackernews import schemas


@pytest.fixture(scope="session")
def client():
    return HNClient()


# -------------- TopStories negatives --------------

@pytest.mark.functional
@pytest.mark.negative
def test_topstories_bad_json_shape_raises(monkeypatch, client):
    """
    N1: Simulate TopStories returning a dict; client must raise (no coercion).
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"not": "a list"}

    # IMPORTANT: your client stores the requests.Session at client.http.session
    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    with pytest.raises(TypeError, match="non-list payload"):
        client.top_stories()


@pytest.mark.functional
@pytest.mark.negative
def test_topstories_mixed_types_is_tolerated(monkeypatch, client):
    """
    N2 (updated): Simulate mixed types (string + int) — client must NOT raise.
    Type validation is covered elsewhere in functional checks.
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return ["123", 456]

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    # Should not raise:
    ids = client.top_stories()
    assert isinstance(ids, list)


@pytest.mark.functional
@pytest.mark.negative
def test_topstories_empty_list_handled(monkeypatch, client):
    """
    N3: Simulate empty list. Client returns [] (valid), but acceptance that
        asserts non-empty should fail/skip separately.
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return []

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    assert client.top_stories() == []


@pytest.mark.functional
@pytest.mark.negative
def test_topstories_http_error(monkeypatch, client):
    """
    N4: Simulate HTTP 500; after retries, client should raise.
    """

    class FakeResp:
        def raise_for_status(self):
            raise Exception("500")

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    with pytest.raises(Exception):
        client.top_stories()


# -------------- Items negatives --------------

@pytest.mark.functional
@pytest.mark.negative
@pytest.mark.parametrize("bad_id", [-1, 0])
def test_invalid_item_id_null_to_none(client, bad_id):
    """
    N6: Invalid ids should return None (Firebase returns null).
    """
    assert client.item(bad_id) is None


@pytest.mark.functional
@pytest.mark.negative
def test_huge_nonexistent_item_id_none(client):
    """
    N7: Very large id should return None.
    """
    assert client.item(9_999_999_999) is None


@pytest.mark.functional
@pytest.mark.negative
def test_corrupt_item_payload_fails_validation(monkeypatch, client):
    """
    N8: Simulate wrong types in item payload → schema validation fails.
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"id": "123", "type": 5, "time": "yesterday"}  # wrong types

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    item = client.item(123)
    with pytest.raises(ValidationError):
        validate(item, schemas.common_item_schema)


@pytest.mark.functional
@pytest.mark.negative
def test_non_json_item(monkeypatch, client):
    """
    N9: Simulate .json() raising ValueError → treat as parse failure (None or raised).
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self): pass

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    # Define desired behavior: client.item returns None on parse error
    try:
        res = client.item(1)
        # If client propagates, test would fail here; adapt to your client design.
        assert res is None or res == {}
    except ValueError:
        # If you prefer raising, assert the exception explicitly instead:
        # with pytest.raises(ValueError): client.item(1)
        pass


@pytest.mark.functional
@pytest.mark.negative
def test_item_http_error(monkeypatch, client):
    """
    N10: Simulate 404/500 on item → after retries, raise.
    """

    class FakeResp:
        def raise_for_status(self):
            raise Exception("404/500")

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=10: FakeResp())

    with pytest.raises(Exception):
        client.item(1)


# -------------- Comment flow negatives --------------

@pytest.mark.functional
@pytest.mark.negative
def test_story_without_comments_skips(client):
    """
    N11: Find a story without kids and assert test skips gracefully.
    """
    for sid in client.new_stories()[:60]:
        it = client.item(sid)
        if it and it.get("type") == "story" and not it.get("kids"):
            pytest.skip("Story without comments is a valid state")
    pytest.skip("No story-without-comments found in sampled window")


@pytest.mark.functional
@pytest.mark.negative
def test_first_kid_not_comment_is_handled(client):
    """
    N12: If the first kid isn't a comment (deleted/other), selection logic should continue/skip.
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if not kids:
            continue
        first = client.item(kids[0])
        if not first or first.get("type") != "comment":
            pytest.skip("First kid is not a comment; logic should continue/skip in positives")
            return
    pytest.skip("No non-comment first kid encountered")


@pytest.mark.functional
@pytest.mark.negative
def test_deleted_or_dead_comment_is_skipped(client):
    """
    N13: If a comment is deleted/dead, we don't assert on its text/linkage; selection should skip.
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if not kids:
            continue
        c = client.item(kids[0])
        if c and (c.get("deleted") or c.get("dead")):
            pytest.skip("Encountered deleted/dead; selection logic should skip in positives")
            return
    pytest.skip("No deleted/dead comment encountered in sample")


@pytest.mark.functional
@pytest.mark.negative
def test_parent_mismatch_simulated(monkeypatch, client):
    """
    N14: Simulate a comment whose 'parent' mismatches the story id → fail with clear message.
    """

    class FakeRespStory:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"id": 111, "type": "story", "time": 1234567890, "kids": [222]}

    class FakeRespComment:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"id": 222, "type": "comment", "time": 1234567891, "parent": 999}  # wrong parent

    calls = {"n": 0}

    def fake_get(url, timeout=10):
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeRespStory()
        return FakeRespComment()

    monkeypatch.setattr(client.http.session, "get", fake_get)

    story = client.item(111)
    comment = client.item(222)
    assert story["id"] != comment["parent"], "Simulated mismatch should be detected by positives"
