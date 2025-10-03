import os
import time
from typing import Any, Dict, List, Optional
import requests

DEFAULT_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class RetrySession:
    def __init__(self, retries: int = 3, backoff: float = 0.5, timeout: float = 5.0):
        self.session = requests.Session()
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> requests.Response:
        timeout = kwargs.pop("timeout", self.timeout)
        last_exc = None
        for attempt in range(self.retries + 1):
            try:
                resp = self.session.get(url, timeout=timeout, **kwargs)
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"Server error {resp.status_code}")
                return resp
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                last_exc = e
                if attempt == self.retries:
                    raise
                time.sleep(self.backoff * (2 ** attempt))
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry loop exit")


class HackerNewsClient:
    def __init__(self, base_url: Optional[str] = None, retries: int = 3, backoff: float = 0.5, timeout: float = 5.0):
        self.base_url = (base_url or os.getenv("HACKERNEWS_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.http = RetrySession(retries=retries, backoff=backoff, timeout=timeout)

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _get_json(self, path: str) -> Any:
        resp = self.http.get(self._url(path))
        resp.raise_for_status()
        return resp.json()

    # ---- list endpoints: ensure list shape only; no element validation/coercion
    def top_stories(self) -> List[Any]:
        data = self._get_json("/topstories.json")
        if not isinstance(data, list):
            raise TypeError(f"topstories returned non-list payload: {type(data).__name__}")
        return data  # may contain non-ints; tests will assert element types

    def new_stories(self) -> List[Any]:
        data = self._get_json("/newstories.json")
        if not isinstance(data, list):
            raise TypeError(f"newstories returned non-list payload: {type(data).__name__}")
        return data

    def best_stories(self) -> List[Any]:
        data = self._get_json("/beststories.json")
        if not isinstance(data, list):
            raise TypeError(f"beststories returned non-list payload: {type(data).__name__}")
        return data

    # ---- item endpoint: return dict or None; no field coercion
    def item(self, id: int) -> Optional[Dict[str, Any]]:
        resp = self.http.get(self._url(f"/item/{int(id)}.json"))
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def first_comment_ids(self, story: Dict[str, Any]) -> List[Any]:
        kids = story.get("kids") or []
        return kids if isinstance(kids, list) else []
