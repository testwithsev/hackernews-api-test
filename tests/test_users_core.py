import random, pytest
from jsonschema import validate
from hackernews import schemas
import string


@pytest.mark.positive
def test_user_schema_from_updates_profile(client):
    up = client._get_json("/updates.json") or {}
    profiles = up.get("profiles") or []
    if not profiles:
        pytest.skip("No profiles available in updates to sample")

    uid = random.choice(profiles)
    user = client._get_json(f"/user/{uid}.json")
    assert user and user.get("id") == uid
    validate(user, schemas.user_schema)
    submitted = user.get("submitted", [])
    assert all(isinstance(x, int) for x in submitted)


@pytest.mark.negative
def test_unknown_user_returns_null_or_empty(client):
    user = client._get_json("/user/__this_should_not_exist__.json")
    assert user is None or user == {}


@pytest.mark.negative
def test_randomized_unknown_user_returns_null_or_empty(client):
    """
    Generate a non-existing random  username
    assert null (None) or empty dict.
    """
    rid = "zzzz_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
    user = client._get_json(f"/user/{rid}.json")
    assert user is None or user == {}
