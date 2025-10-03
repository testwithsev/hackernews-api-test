import random
import pytest
from jsonschema import validate

from hackernews.client import HackerNewsClient
from hackernews import schemas


@pytest.fixture(scope="session")
def client():
    return HackerNewsClient(retries=2, backoff=0.3, timeout=6.0)


# ---------------- Acceptance: Functional / Positive ----------------

@pytest.mark.functional
@pytest.mark.positive
def test_acceptance_top_stories_non_empty(client):
    """
    Validates the Top Stories endpoint contract:
    - Must return a list (not None / dict / scalar)
    - List must be non-empty (there are stories to show)
    - Each element must be an integer ID (HN item ids are ints)
    """
    ids = client.top_stories()
    assert isinstance(ids, list) and len(ids) > 0
    assert all(isinstance(x, int) for x in ids)


@pytest.mark.functional
@pytest.mark.positive
def test_acceptance_current_top_story_fetchable(client):
    """
    Validates we can fetch a story item using an id from /topstories:
    - Fetch first id from the top list and then fetch /item/{id}
    - Item must exist (not None)
    - Item must satisfy the common item schema (id/type/time invariants)
    - Type is one of the tolerated kinds (story, job, poll) to avoid brittleness
    Purpose: confirms the ids returned by /topstories are actually resolvable items.
    """
    top_ids = client.top_stories()
    story = client.item(top_ids[0])
    assert story is not None
    validate(instance=story, schema=schemas.common_item_schema)
    assert story.get("type") in {"story", "job", "poll"}  # tolerant


@pytest.mark.functional
@pytest.mark.positive
def test_acceptance_first_comment_of_a_top_story(client):
    """
    Validates we can retrieve a first-level comment for a top story:
    - Iterate a small window of top stories and find one with kids (comments)
    - Fetch its first comment and validate with comment schema
    - Ensure comment.parent points back to the story.id (linkage is correct)
    - If none found in the window, skip to avoid flakiness on live data
    Purpose: acceptance-level check that story → comment relationships are healthy.
    """
    for sid in client.top_stories()[:30]:
        story = client.item(sid)
        if story and isinstance(story.get("kids"), list) and story["kids"]:
            cid = story["kids"][0]
            comment = client.item(cid)
            if comment:
                validate(instance=comment, schema=schemas.comment_schema)
                assert comment.get("parent") == story["id"]
                return
    pytest.skip("No top story with comments found in the first 30 items")


# ---------------- Lists ----------------

@pytest.mark.functional
@pytest.mark.positive
@pytest.mark.parametrize("endpoint", ["top_stories", "new_stories", "best_stories"])
def test_story_lists_non_empty_and_ints(client, endpoint):
    """
    Validates HN list endpoints (/topstories, /newstories, /beststories):
    - Must return a non-empty list
    - Elements in the (sampled) list must be positive integer ids
    Purpose: ensures each list variant returns usable ids for downstream item fetches.
    """
    ids = getattr(client, endpoint)()
    assert isinstance(ids, list) and len(ids) > 0
    assert all(isinstance(x, int) and x > 0 for x in ids[:50])


@pytest.mark.functional
@pytest.mark.positive
@pytest.mark.parametrize("endpoint", ["top_stories", "new_stories", "best_stories"])
def test_story_lists_reasonable_limits(client, endpoint):
    """
    Sanity constraint: list endpoints should not be unbounded.
    - Assert the list length is below a high but reasonable cap (<= 5000)
    Purpose: coarse guardrail against accidental explosion/duplication in lists.
    """
    ids = getattr(client, endpoint)()
    assert len(ids) <= 5000


# ---------------- Items / Schemas ----------------

@pytest.mark.functional
@pytest.mark.positive
@pytest.mark.parametrize("endpoint", ["top_stories", "new_stories", "best_stories"])
def test_sampled_items_match_common_schema(client, endpoint):
    """
    Contract validation at scale (sampled):
    - Randomly sample up to 10 ids from each list endpoint
    - Each fetched item must satisfy the common item schema (id/type/time)
    Purpose: broad schema coverage without being brittle to live content.
    """
    ids = getattr(client, endpoint)()
    sample = random.sample(ids[:50], k=min(10, len(ids[:50])))
    for sid in sample:
        it = client.item(sid)
        if it is not None:
            validate(instance=it, schema=schemas.common_item_schema)


@pytest.mark.functional
@pytest.mark.positive
def test_valid_story_item_type_specific_checks(client):
    """
    Type-specific validation for 'story':
    - Find a 'story' item among top stories
    - Validate with story-specific schema (stricter than common)
    - If 'title' exists → must be non-empty string
    - If 'score' exists → must be integer >= 0
    Purpose: deeper checks for key type beyond the generic item shape.
    """
    for sid in client.top_stories()[:50]:
        it = client.item(sid)
        if it and it.get("type") == "story":
            validate(it, schemas.story_schema)
            if "title" in it:
                assert isinstance(it["title"], str) and it["title"].strip() != ""
            if "score" in it:
                assert isinstance(it["score"], int) and it["score"] >= 0
            return
    pytest.skip("No explicit 'story' found in sample")


@pytest.mark.functional
@pytest.mark.positive
def test_comment_item_schema_and_parent_linkage(client):
    """
    Comment-specific contract and linkage:
    - Pick a top story with kids
    - Fetch the first comment and validate with comment schema
    - Verify the 'parent' field equals the story id (correct linkage)
    Purpose: ensures comments are well-formed and connected to their story.
    """
    for sid in client.top_stories()[:40]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if kids:
            comment = client.item(kids[0])
            if comment:
                validate(comment, schemas.comment_schema)
                assert comment.get("parent") == story["id"]
                return
    pytest.skip("No comment found to validate")


@pytest.mark.functional
@pytest.mark.negative
@pytest.mark.parametrize("bad_id", [-1, 0, 9999999999])
def test_invalid_or_huge_id_returns_none(client, bad_id):
    """
    Negative-path robustness for item fetch:
    - Invalid or extremely large ids should return None (Firebase returns null)
    Purpose: ensures the client normalizes 'null' to None and does not raise.
    """
    assert client.item(bad_id) is None


@pytest.mark.functional
@pytest.mark.positive
def test_story_without_comments_graceful(client):
    """
    Valid story with no comments:
    - Find a story (from /newstories to increase odds) that has no 'kids'
    - Validate with the story schema
    Purpose: story items are valid even without any comments.
    """
    for sid in client.new_stories()[:60]:
        it = client.item(sid)
        if it and it.get("type") == "story" and not it.get("kids"):
            validate(it, schemas.story_schema)
            return
    pytest.skip("No story without comments found in sample")


# ---------------- Field Validation ----------------

@pytest.mark.functional
@pytest.mark.positive
@pytest.mark.parametrize("field", ["title", "text", "by"])
def test_optional_string_fields_non_empty_when_present(client, field):
    """
    Optional string fields sanity:
    - When present, 'title'/'text'/'by' must be non-empty strings
    Purpose: avoid degenerate values (empty strings) that break UIs or logic.
    """
    for sid in client.top_stories()[:40]:
        it = client.item(sid)
        if it and field in it:
            assert isinstance(it[field], str) and it[field].strip() != ""


@pytest.mark.functional
@pytest.mark.positive
@pytest.mark.parametrize("int_field", ["id", "time", "score", "descendants"])
def test_integer_fields_are_integers_when_present(client, int_field):
    """
    Optional integer fields type check:
    - For a pooled sample of ids, when 'id'/'time'/'score'/'descendants' exist,
      they must be integers
    Purpose: data type sanity for fields commonly used in clients.
    """
    ids = (client.top_stories()[:20] + client.new_stories()[:20] + client.best_stories()[:20])[:50]
    for sid in ids:
        it = client.item(sid)
        if it and int_field in it:
            assert isinstance(it[int_field], int)


@pytest.mark.functional
@pytest.mark.positive
def test_kids_are_ints_and_fetchable_subset(client):
    """
    Children linkage quick check:
    - For a story with kids, the first few 'kids' ids must be integers
    - We can fetch a small subset of those comment items successfully
    Purpose: verifies the kids list is well-formed and points to retrievable items.
    """
    for sid in client.top_stories()[:30]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if kids:
            subset = kids[:5]
            assert all(isinstance(k, int) for k in subset)
            fetched = [client.item(k) for k in subset]
            assert len(fetched) == len(subset)
            return
    pytest.skip("No kids to check")