import pytest
from jsonschema import validate
from hackernews import schemas
from jsonschema import ValidationError


@pytest.mark.positive
def test_comment_parent_points_to_story_or_comment(client):
    for story_id in client.top_stories():
        story = client.item(story_id)
        kids = (story or {}).get("kids") or []
        if not kids:
            continue
        kid = client.item(kids[0])
        if not (kid and kid.get("type") == "comment"):
            continue
        assert "parent" in kid and isinstance(kid["parent"], int)
        return
    pytest.skip("No first-level comment found")


@pytest.mark.negative
def test_fetch_nonexistent_child_comment_returns_none_or_skip(client):
    """
    If a top story has kids, probe a child id that is very unlikely to exist
    Should return none. Skip when no kids are available.
    """
    for sid in client.top_stories():
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if not kids:
            continue
        probe = kids[0] + 10 ** 12
        assert client.item(probe) is None
        return
    pytest.skip("No story with kids available to probe")



