import time
import random
import pytest
from jsonschema import validate
from hackernews import schemas


@pytest.mark.positive
def test_common_item_schema_sampled_across_lists(client):
    pool = client.top_stories() + client.new_stories() + client.best_stories()
    if not pool:
        pytest.skip("No items available to sample")
    sample = random.sample(pool, min(12, len(pool)))
    for item_id in sample:
        it = client.item(item_id)
        if it is not None:
            validate(it, schemas.common_item_schema)
            assert 0 < it["time"] <= int(time.time()) + 300


@pytest.mark.positive
def test_story_optional_fields_when_present(client):
    for item_id in client.top_stories():
        item = client.item(item_id)
        if not item or item.get("type") != "story":
            continue
        if "title" in item:
            assert isinstance(item["title"], str) and item["title"].strip()
        if "url" in item:
            assert isinstance(item["url"], str) and item["url"].strip()
        if "score" in item:
            assert isinstance(item["score"], int) and item["score"] >= 0
        if "descendants" in item:
            assert isinstance(item["descendants"], int) and item["descendants"] >= 0
        return
    pytest.skip("No story found in sample")


@pytest.mark.positive
def test_kids_subset_fetchable_and_ints(client):
    for item_id in client.top_stories():
        story = client.item(item_id)
        kids = (story or {}).get("kids") or []
        if kids:
            subset = kids[: min(5, len(kids))]
            assert all(isinstance(k, int) for k in subset)
            fetched = [client.item(k) for k in subset]
            assert len(fetched) == len(subset)
            return
    pytest.skip("No story with kids in the window")


@pytest.mark.negative
@pytest.mark.parametrize("bad_id", [-10, -1, 0, 10 ** 18])
def test_item_out_of_range_ids_return_none(client, bad_id):
    """Invalid/huge IDs should return null"""
    assert client.item(bad_id) is None


@pytest.mark.negative
def test_item_maxitem_plus_offsets_return_none(client):
    """
    The largest existing id is /maxtiem. Probing ahead (max+1, max+10, max+100)
    should be null -> client returns None.
    """
    max_id = client._get_json("/maxitem.json")
    assert isinstance(max_id, int) and max_id > 0
    for off in (1, 10, 100):
        assert client.item(max_id + off) is None
