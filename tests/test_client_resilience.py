import pytest
from jsonschema import validate
from hackernews import schemas
from jsonschema import ValidationError


@pytest.mark.negative
def test_topstories_bad_json_shape_raises(monkeypatch, client):
    class R:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"not": "a list"}  # wrong shape

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=5.0: R())

    with pytest.raises(TypeError, match="non-list payload"):
        client.top_stories()


@pytest.mark.negative
def test_comment_missing_parent_fails_schema(monkeypatch, client):
    # comment must include 'parent'
    class R:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"id": 2, "type": "comment", "time": 1_700_000_001}

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=5.0: R())

    c = client.item(2)
    with pytest.raises(ValidationError):
        validate(c, schemas.comment_schema)


@pytest.mark.negative
def test_item_corrupt_payload_fails_schema(monkeypatch, client):
    # required fields have wrong types -> schema must reject
    class R:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return {"id": "abc", "type": 123, "time": "yesterday"}

    monkeypatch.setattr(client.http.session, "get", lambda url, timeout=5.0: R())

    it = client.item(123)
    with pytest.raises(ValidationError):
        validate(it, schemas.common_item_schema)
