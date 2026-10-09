from pgvector.django import CosineDistance
from api.models import IsoControl
from services.search.engines.base import BaseSearchEngine
from services.search.selectors import get_embedding_provider
from services.search.helpers import annotate_result

class VectorSearchEngine(BaseSearchEngine):
    def search(self, query_text: str, top_k: int = 5):
        provider = get_embedding_provider()
        query_vector = provider.get_embedding(query_text)

        results = list(
            IsoControl.objects
            .exclude(embedding__isnull=True)
            .annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")[:top_k]
        )

        for control in results:
            annotate_result(control, 1.0 - float(control.distance), "cosine_similarity")
        return results
