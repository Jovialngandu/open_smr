
from django.conf import settings

# Sélecteur d'embeddings (Pas de boucle ici, on peut les laisser en haut)
from services.search.embeddings.huggingface import HuggingFaceEmbeddingProvider
from services.search.embeddings.local import LocalEmbeddingProvider

def get_embedding_provider():
    if settings.EMBEDDING_ENGINE == "huggingface":
        return HuggingFaceEmbeddingProvider()
    elif settings.EMBEDDING_ENGINE == "local":
        return LocalEmbeddingProvider()
    raise ValueError(f"Engine d'embedding inconnu : {settings.EMBEDDING_ENGINE}")


# Sélecteur de moteur de recherche
def get_search_engine():
    # Les imports sont mis ici pour Casser la boucle circulaire !
    from services.search.engines.vector import VectorSearchEngine
    from services.search.engines.bm25 import BM25SearchEngine
    from services.search.engines.hybrid import HybridSearchEngine

    engine = getattr(settings, "SOA_SEARCH_ENGINE", "vector").lower()

    engines = {
        "vector": VectorSearchEngine,
        "bm25": BM25SearchEngine,
        "hybrid": HybridSearchEngine,
    }

    try:
        return engines[engine]()
    except KeyError:
        raise ValueError(f"Moteur de recherche SoA inconnu : {engine}")


def search_soa_controls(query_text: str, top_k: int = 5):
    """Point d'entrée unique et stable pour l'API extérieure."""
    if not isinstance(query_text, str) or not query_text.strip():
        return []
    if top_k < 1:
        return []

    engine = get_search_engine()
    return engine.search(query_text.strip(), top_k=top_k)

