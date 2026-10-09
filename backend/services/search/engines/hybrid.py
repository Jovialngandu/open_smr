from services.search.engines.base import BaseSearchEngine
from services.search.engines.vector import VectorSearchEngine
from services.search.engines.bm25 import BM25SearchEngine
from services.search.helpers import annotate_result

RRF_K = 60

class HybridSearchEngine(BaseSearchEngine):
    def __init__(self, rrf_k: int = RRF_K, candidate_multiplier: int = 4):
        self.rrf_k = rrf_k
        self.candidate_multiplier = candidate_multiplier

    def search(self, query_text: str, top_k: int = 5):
        candidate_k = max(20, top_k * self.candidate_multiplier)

        vector_results = VectorSearchEngine().search(query_text, top_k=candidate_k)
        bm25_results = BM25SearchEngine().search(query_text, top_k=candidate_k)

        fused_scores = {}
        controls_by_id = {}

        for results in (vector_results, bm25_results):
            for rank, control in enumerate(results, start=1):
                control_id = control.pk
                controls_by_id[control_id] = control
                fused_scores[control_id] = fused_scores.get(control_id, 0.0) + 1.0 / (self.rrf_k + rank)

        ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        return [annotate_result(controls_by_id[cid], fused_scores[cid], "rrf") for cid in ranked_ids]
