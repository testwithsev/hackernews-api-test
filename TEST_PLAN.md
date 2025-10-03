# Test Plan — HackerNews API (Positive & Negative)

## Scope
Covers HackerNews public API endpoints:
- `GET /topstories.json`
- `GET /newstories.json`
- `GET /beststories.json`
- `GET /item/{id}.json`

Focus: **functional positives and negatives** (not performance).

## Conventions
- No type coercion in the client. Validate real server output.
- Use schema validation (common item, comment, and optionally story).
- For live-data dependencies (e.g., “story with kids”), search a small window and **skip** if not found.
- Markers:
  - `@pytest.mark.positive`
  - `@pytest.mark.negative`
  - `@pytest.mark.functional`
  - `@pytest.mark.smoke` (for small fast checks)

## Positive Cases

P1 — **TopStories returns a list**  
P2 — **TopStories non-empty**  
P3 — **TopStories elements are integers (no coercion)**  
P4 — **TopStories content-type is JSON**  
P5 — **TopStories reasonable upper bound (<= 5000)**  
P6 — **TopStories IDs unique (sample / whole)**  
P7 — **Fetch current top story item (id/type/time present; type tolerant)**  
P8 — **Story-specific fields when present (title non-empty, score >= 0, descendants >= 0)**  
P9 — **Timestamp sanity (0 < time <= now + 300s)**  
P10 — **Multiple items spot-check (sample 10 across lists) vs common schema**  
P11 — **Kids list shape (ints) and subset fetchable**  
P12 — **Type tolerance: job/poll items still satisfy common schema**  
P13 — **First comment of a top story (comment schema + parent linkage)**  
P14 — **Comment optional fields (text/by) are non-empty if present**  
P15 — **Two-level nesting sanity (if present): comment-of-comment contract**  
P16 — **Unicode/HTML text is a string; no crashes**

## Negative Cases

N1 — **Bad JSON shape for TopStories (simulate)** → TypeError  
N2 — **Mixed types in TopStories (simulate)** → TypeError  
N3 — **Empty TopStories list (simulate)** → acceptance fails/skip with clear msg  
N4 — **Non-200 / timeout on TopStories (simulate)** → retries then Request/HTTPError  
N5 — **Wrong path (manual raw GET)** → 404

N6 — **Invalid item id −1/0** → `null` → client `None`  
N7 — **Huge non-existent id** → `null` → client `None`  
N8 — **Corrupt item payload (simulate)** → jsonschema validation error  
N9 — **Non-JSON body on item (simulate)** → parse error/None (assert predictable behavior)  
N10 — **404/500 on item (simulate)** → retries then HTTPError

N11 — **Story without comments** → skip (valid state)  
N12 — **First kid isn’t a comment (e.g., deleted)** → selection logic handles or skip  
N13 — **Deleted/dead comment** → selection logic handles or skip  
N14 — **Parent mismatch (simulate)** → fail with “linkage broken”
