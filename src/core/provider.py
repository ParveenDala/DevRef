from typing import List, Dict, Optional

import httpx
import yaml

from .search import SearchResult


class BaseProvider:
    name = "base"

    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        raise NotImplementedError


class InternalProvider(BaseProvider):
    name = "internal"

    def __init__(self, seed: Optional[Dict] = None):
        self.seed = seed or {}

    @classmethod
    def from_yaml(cls, path_or_file):
        if hasattr(path_or_file, "read"):
            content = path_or_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            data = yaml.safe_load(content)
        else:
            with open(path_or_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        return cls(seed=data or {})

    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        key = query.lower().strip()
        hits = []
        for kx, items in self.seed.items():
            if key in kx.lower() or kx.lower() in key:
                for it in items:
                    hits.append(SearchResult(
                        title=str(it.get("title", "")),
                        url=str(it.get("url", "")),
                        snippet=str(it.get("snippet", "")) if it.get("snippet") else "",
                        source=self.name
                    ))
        return hits[:k]


class GoogleProvider(BaseProvider):
    name = "google"

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        self.api_key = api_key
        self.cse_id = cse_id

    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        if not self.api_key or not self.cse_id:
            return []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"q": query, "key": self.api_key, "cx": self.cse_id, "num": min(k, 10)}
        try:
            with httpx.Client(timeout=15.0) as client:
                r = client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            return []

        items = data.get("items", []) or []
        out: List[SearchResult] = []
        for it in items[:k]:
            try:
                title = str(it.get("title", "") or "")
                link = str(it.get("link", "") or "")
                snippet = str(it.get("snippet", "") or "")
                out.append(SearchResult(title=title, url=link, snippet=snippet, source=self.name))
            except Exception:
                continue
        return out


class YouTubeProvider(BaseProvider):
    name = "youtube"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"q": query, "key": self.api_key, "part": "snippet", "type": "video", "maxResults": min(k, 10)}
        try:
            with httpx.Client(timeout=15.0) as client:
                r = client.get(url, params=params)
                if r.status_code != 200:
                    return []
                data = r.json()
        except Exception as e:
            return []

        items = data.get("items", []) or []
        out: List[SearchResult] = []
        for it in items[:k]:
            try:
                sn = it.get("snippet") or {}
                vid = (it.get("id") or {}).get("videoId")
                title = str(sn.get("title", "") or "")
                desc = str(sn.get("description", "") or "")
                link = f"https://www.youtube.com/watch?v={vid}" if vid else ""
                out.append(SearchResult(title=title, url=link, snippet=desc, source=self.name,
                                        date=str(sn.get("publishTime")) if sn.get("publishTime") else None))
            except Exception:
                continue
        return out
