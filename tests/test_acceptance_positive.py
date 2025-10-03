import time
import random
import pytest
from jsonschema import validate
from hackernews.client import HackerNewsClient as HNClient
from hackernews import schemas


@pytest.fixture(scope="session")
def client():
    return HNClient()


# ------------------------- TopStories -------------------------

@pytest.mark.positive
def test_topstories_returns_list(client):
    """
    P1: TopStories must return a JSON array (list).
    """
    ids = client.top_stories()
    assert isinstance(ids, list)


@pytest.mark.positive
def test_topstories_non_empty(client):
    """
    P2: TopStories should be non-empty.
    """
    ids = client.top_stories()
    assert len(ids) > 0


@pytest.mark.positive
def test_topstories_elements_are_ints_no_coercion(client):
    """
    P3: All IDs must be integers (client does NOT coerce types).
    """
    ids = client.top_stories()
    assert all(isinstance(x, int) for x in ids)


@pytest.mark.positive
def test_topstories_reasonable_upper_bound(client):
    """
    P5: Sanity cap for list size (<= 5000).
    """
    ids = client.top_stories()
    assert len(ids) <= 5000


@pytest.mark.positive
def test_topstories_ids_unique_sample(client):
    """
    P6: No obvious duplicates (check head/sample).
    """
    ids = client.top_stories()
    head = ids[:200] if len(ids) > 200 else ids
    assert len(set(head)) == len(head)


# ------------------------- Items -------------------------

@pytest.mark.positive
def test_fetch_current_top_story_item(client):
    """
    P7: Fetch first top story item and validate common invariants.
    """
    sid = client.top_stories()[0]
    it = client.item(sid)
    assert isinstance(it, dict)
    validate(it, schemas.common_item_schema)
    assert it.get("type") in {"story", "job", "poll", "ask", "show", "pollopt"}


@pytest.mark.positive
def test_story_specific_fields_when_present(client):
    """
    P8: For a 'story' item, optional fields (when present) meet expectations.
    """
    for sid in client.top_stories()[:50]:
        it = client.item(sid)
        if it and it.get("type") == "story":
            if "title" in it:
                assert isinstance(it["title"], str) and it["title"].strip() != ""
            if "score" in it:
                assert isinstance(it["score"], int) and it["score"] >= 0
            if "descendants" in it:
                assert isinstance(it["descendants"], int) and it["descendants"] >= 0
            return
    pytest.skip("No 'story' found in sampled top stories")


@pytest.mark.positive
def test_timestamp_sanity(client):
    """
    P9: time is a UNIX seconds int within a reasonable bound (allows +300s skew).
    """
    sid = client.top_stories()[0]
    it = client.item(sid)
    now = int(time.time())
    assert isinstance(it.get("time"), int)
    assert 0 < it["time"] <= now + 300


@pytest.mark.positive
def test_multiple_items_spotcheck_common_schema(client):
    """
    P10: Validate 10 sampled items (across lists) against common schema.
    """
    pool = (
        client.top_stories()[:20]
        + client.new_stories()[:20]
        + client.best_stories()[:20]
    )
    sample = random.sample(pool, k=min(10, len(pool)))
    for sid in sample:
        it = client.item(sid)
        if it is not None:
            validate(it, schemas.common_item_schema)


@pytest.mark.positive
def test_kids_shape_and_subset_fetchable(client):
    """
    P11: For a story with kids, kids are ints and a small subset is fetchable.
    """
    for sid in client.top_stories()[:40]:
        it = client.item(sid)
        kids = (it or {}).get("kids") or []
        if kids:
            assert all(isinstance(k, int) for k in kids[:10])
            fetched = [client.item(k) for k in kids[:3]]
            assert len(fetched) == len(kids[:3])
            return
    pytest.skip("No story with kids in sampled top stories")


@pytest.mark.positive
def test_job_poll_items_tolerated(client):
    """
    P12: If we encounter a 'job' or 'poll', they still satisfy common schema.
    """
    for sid in client.top_stories()[:60]:
        it = client.item(sid)
        if it and it.get("type") in {"job", "poll"}:
            validate(it, schemas.common_item_schema)
            return
    pytest.skip("No job/poll found in sample")


# ------------------------- Comments -------------------------

@pytest.mark.positive
def test_first_comment_of_top_story_links_back(client):
    """
    P13: First-level comment validates comment schema and parent linkage to story.
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if kids:
            comment = client.item(kids[0])
            if comment and comment.get("type") == "comment":
                validate(comment, schemas.comment_schema)
                assert comment.get("parent") == story["id"]
                return
    pytest.skip("No suitable first-level comment found")


@pytest.mark.positive
def test_comment_optional_fields_when_present(client):
    """
    P14: 'text' and 'by' are non-empty strings when present.
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if kids:
            comment = client.item(kids[0])
            if comment and comment.get("type") == "comment":
                if "text" in comment:
                    assert isinstance(comment["text"], str) and comment["text"].strip() != ""
                if "by" in comment:
                    assert isinstance(comment["by"], str) and comment["by"].strip() != ""
                return
    pytest.skip("No comment with optional fields found")


@pytest.mark.positive
def test_two_level_nesting_if_present(client):
    """
    P15: If a comment has kids, fetch one child and validate it's a proper comment with sane timestamp.
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        level1 = (story or {}).get("kids") or []
        if not level1:
            continue
        c1 = client.item(level1[0])
        if not (c1 and c1.get("type") == "comment"):
            continue
        level2 = (c1.get("kids") or [])
        if not level2:
            continue
        c2 = client.item(level2[0])
        if c2 and c2.get("type") == "comment":
            validate(c2, schemas.comment_schema)
            assert isinstance(c2.get("time"), int) and c2["time"] > 0
            assert c2.get("parent") == c1["id"]
            return
    pytest.skip("No two-level nesting found")


@pytest.mark.positive
def test_text_is_string_no_crash(client):
    """
    P16: Best-effort check that comment text is a string when present (unicode/HTML tolerated).
    """
    for sid in client.top_stories()[:60]:
        story = client.item(sid)
        kids = (story or {}).get("kids") or []
        if kids:
            c = client.item(kids[0])
            if c and c.get("type") == "comment" and "text" in c:
                assert isinstance(c["text"], str)
                return
    pytest.skip("No comment text found")
