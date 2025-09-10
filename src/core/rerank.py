from typing import List

from .search import SearchResult


def score_pair(query_text: str, candidate: SearchResult) -> float:
    qs = set(query_text.lower().split())
    cs = set((candidate.title + " " + candidate.snippet).lower().split())
    if not qs or not cs:
        return 0.0
    return len(qs & cs) / len(qs)


def rerank(query_text: str, candidates: List[SearchResult], top_k: int = 5) -> List[dict]:
    scored = [(c, score_pair(query_text, c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"title": c.title, "url": c.url, "snippet": c.snippet, "score": float(s), "source": c.source} for c, s in
            scored[:top_k]]
