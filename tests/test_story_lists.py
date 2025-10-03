import pytest
from jsonschema import validate
from hackernews import schemas


@pytest.mark.positive
@pytest.mark.parametrize("list_method, limit", [
    ("top_stories", 500), ("new_stories", 500), ("best_stories", 500),
    ("ask_stories", 200), ("show_stories", 200), ("job_stories", 200),
])
def test_lists_non_empty_ints_and_bounds(client, list_method, limit):
    ids = getattr(client, list_method)()
    assert isinstance(ids, list) and len(ids) > 0
    assert len(ids) <= limit
    assert all(isinstance(x, int) for x in ids)


@pytest.mark.positive
@pytest.mark.parametrize("list_method, expected_type", [
    ("ask_stories", "story"), ("show_stories", "story"), ("job_stories", "job"),
])
def test_ask_show_job_sample_types(client, list_method, expected_type):
    ids = getattr(client, list_method)()
    for item_id in ids[: min(5, len(ids))]:
        it = client.item(item_id)
        validate(it, schemas.common_item_schema)
        assert it.get("type") == expected_type


@pytest.mark.positive
@pytest.mark.parametrize("list_method", [
    "top_stories", "new_stories", "best_stories",
    "ask_stories", "show_stories", "job_stories",
])
def test_lists_have_strictly_unique_ids(client, list_method):
    ids = getattr(client, list_method)()
    assert len(ids) == len(set(ids)), f"Duplicates found in {list_method}"



