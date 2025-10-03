import pytest


@pytest.mark.positive
def test_maxitem_covers_all_lists_combined(client):
    lists = ["top_stories", "new_stories", "best_stories",
             "ask_stories", "show_stories", "job_stories"]
    all_ids = []
    for name in lists:
        all_ids.extend(getattr(client, name)())

    if not all_ids:
        pytest.skip("No IDs across any list")

    list_max = max(all_ids)
    max_id = client._get_json("/maxitem.json")
    if isinstance(max_id, int) and max_id < list_max:
        max_id = client._get_json("/maxitem.json")
    assert isinstance(max_id, int) and max_id >= list_max, \
        f"maxitem={max_id} < max(all_lists)={list_max}"
