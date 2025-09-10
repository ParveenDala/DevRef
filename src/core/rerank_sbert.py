from typing import List, Tuple

from sentence_transformers import SentenceTransformer, util

from .search import SearchResult


class EmbeddingReranker:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def score(self, query_text: str, candidates: List[SearchResult]) -> List[Tuple[SearchResult, float]]:
        if not candidates:
            return []
        cand_texts = [f"{c.title}. {c.snippet}" if c.snippet else c.title for c in candidates]
        q_emb = self.model.encode([query_text], convert_to_tensor=True, normalize_embeddings=True)[0]
        c_embs = self.model.encode(cand_texts, convert_to_tensor=True, normalize_embeddings=True)
        sims = util.cos_sim(q_emb, c_embs).cpu().numpy().flatten().tolist()
        scored = [(candidates[i], float(sims[i])) for i in range(len(candidates))]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
