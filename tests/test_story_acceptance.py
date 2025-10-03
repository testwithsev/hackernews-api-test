import pytest
from jsonschema import validate
from hackernews import schemas


@pytest.mark.positive
def test_fetch_current_top_story_item(client):
    ids = client.top_stories()
    assert ids, "No top stories right now"
    it = client.item(ids[0])
    assert isinstance(it, dict)
    validate(it, schemas.common_item_schema)
    assert it.get("type") in {"story", "job", "poll"}


@pytest.mark.positive
def test_top_story_first_comment_via_items_api(client):
    top_ids = client.top_stories()
    assert top_ids, "no top stories"

    story = client.item(top_ids[0])
    assert story and story.get("type") in {"story", "job", "poll"}

    kids = story.get("kids") or []
    if not kids:
        pytest.skip("top item has no kids (no first-level comments)")

    first = client.item(kids[0])
    if not first or first.get("type") != "comment":
        pytest.skip("first kid is not a comment")

    validate(first, schemas.comment_schema)
    assert first.get("parent") == story["id"]
