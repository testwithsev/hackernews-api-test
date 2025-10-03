import pytest


@pytest.mark.positive
def test_updates_schema_and_sample_fetch(client):
    up = client._get_json("/updates.json")
    assert isinstance(up, dict)
    assert isinstance(up.get("items"), list)
    assert isinstance(up.get("profiles"), list)

    checked = 0
    for item_id in up["items"][:5]:
        if isinstance(item_id, int):
            _ = client.item(item_id)
            checked += 1
    if checked == 0:
        pytest.skip("No integer item IDs in /updates")


@pytest.mark.positive
def test_updates_profiles_are_strings(client):
    up = client._get_json("/updates.json") or {}
    profiles = up.get("profiles") or []
    if profiles:
        assert all(isinstance(p, str) for p in profiles)
    else:
        pytest.skip("No profiles in /updates")
