from django.test import override_settings

from services.search.embeddings.local import LocalEmbeddingProvider
from services.search.selectors import get_embedding_provider


@override_settings(EMBEDDING_ENGINE="local")
def test_local_embedding_provider_is_selected():
    provider = get_embedding_provider()

    assert isinstance(provider, LocalEmbeddingProvider)
    assert provider.dimensions == 384