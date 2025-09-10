import os
from typing import List, Dict, Any

from core.provider import InternalProvider, GoogleProvider, YouTubeProvider
from .nlp import extract_topics, build_queries
from .rerank import rerank as simple_rerank
from .search import SearchResult

try:
    from .rerank_sbert import EmbeddingReranker

    SBERT_AVAILABLE = True
except Exception:
    SBERT_AVAILABLE = False


class Recommender:
    def __init__(self, *, google_cfg: dict = None, youtube_cfg: dict = None):

        self.google_cfg = {
            "api_key": (google_cfg or {}).get("api_key") or os.getenv("GOOGLE_API_KEY"),
            "cse_id": (google_cfg or {}).get("cse_id") or os.getenv("GOOGLE_CSE_KEY")
        }
        self.youtube_cfg = {"api_key": (youtube_cfg or {}).get("api_key") or os.getenv("YOUTUBE_API_KEY")}

        self.reranker = EmbeddingReranker() if SBERT_AVAILABLE else None

    def _resolve_sources(self, names: List[str]) -> List:
        providers = []
        for n in names:
            n_low = n.lower()
            if n_low in "internal":
                seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "internal_dataset.yaml")
                mock_provider = InternalProvider.from_yaml(seed_path)
                providers.append(InternalProvider(seed=mock_provider.seed))
            elif n_low == "google":
                providers.append(
                    GoogleProvider(api_key=self.google_cfg.get("api_key"), cse_id=self.google_cfg.get("cse_id")))
            elif n_low == "youtube":
                providers.append(YouTubeProvider(api_key=self.youtube_cfg.get("api_key")))
            else:
                continue
        return providers

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        comment = payload.get("comment", "") or ""
        tags = payload.get("tags") or []
        settings = payload.get("settings") or {}
        top_k = int(settings.get("num_recommendations", 3))
        source_names = settings.get("sources", ["internal"])
        extracted_topics_dict = extract_topics(comment) or {}
        extracted_topics = extracted_topics_dict.get('topics', [])

        combined_topics = extracted_topics + tags

        processed_extraction = {
            "topics": combined_topics,
            "intents": extracted_topics_dict.get('intents', [])
        }
        print(processed_extraction)

        queries = build_queries(processed_extraction)
        # Deduplicate while keeping order
        unique_queries = []
        seen = set()
        for q in queries:
            qnorm = q.lower().strip()
            if qnorm not in seen:
                seen.add(qnorm)
                unique_queries.append(q)
            if len(unique_queries) == 2:
                break

        queries = unique_queries

        query_text = " ".join(queries) if queries else comment

        providers = self._resolve_sources(source_names)

        warnings = []
        raw_candidates: List[SearchResult] = []

        for prov in providers:
            try:
                for q in queries or [comment]:
                    hits = prov.search(q, k=10)
                    raw_candidates.extend(hits)
            except Exception as e:
                warnings.append(f"Provider {getattr(prov, 'name', str(prov))} error: {e}")

        seen = set()
        merged: List[SearchResult] = []
        for c in raw_candidates:
            if c.url and c.url not in seen:
                merged.append(c)
                seen.add(c.url)
        merged = merged[:200]

        recommendations = []
        if SBERT_AVAILABLE and self.reranker:
            try:
                scored = self.reranker.score(query_text, merged)
                top = scored[:top_k]
                for s in top:
                    recommendations.append({
                        "title": s[0].title,
                        "url": s[0].url,
                        "snippet": s[0].snippet,
                        "score": float(s[1]),
                        "source": s[0].source
                    })
            except Exception as e:
                warnings.append(f"SBERT rerank error: {e}")
                recommendations = simple_rerank(query_text, merged, top_k)
        else:
            recommendations = simple_rerank(query_text, merged, top_k)

        resources = []
        for r in recommendations:
            resources.append({
                "title": r.get("title") if isinstance(r, dict) else getattr(r, "title", ""),
                "url": r.get("url") if isinstance(r, dict) else getattr(r, "url", ""),
                "source": r.get("source") if isinstance(r, dict) else getattr(r, "source", "")
            })
        return {"resources": resources}
