from rank_bm25 import BM25Okapi
from api.models import IsoControl
from services.search.engines.base import BaseSearchEngine


from  services.search.helpers import tokenize, control_search_text, annotate_result

class BM25SearchEngine(BaseSearchEngine):
    def search(self, query_text: str, top_k: int = 5):
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return []

        controls = list(IsoControl.objects.all())
        if not controls:
            return []

        tokenized_documents = [tokenize(control_search_text(control)) for control in controls]
        corpus_tokens = {token for doc in tokenized_documents for token in doc}

        if not any(token in corpus_tokens for token in query_tokens):
            return []

        bm25 = BM25Okapi(tokenized_documents)
        scores = bm25.get_scores(query_tokens)

        ranked_indices = sorted(range(len(controls)), key=lambda i: float(scores[i]), reverse=True)[:top_k]

        return [annotate_result(controls[i], float(scores[i]), "bm25") for i in ranked_indices]
