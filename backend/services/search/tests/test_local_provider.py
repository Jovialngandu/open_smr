import numpy as np
import pytest

from services.search.embeddings.local import LocalEmbeddingProvider


@pytest.fixture(scope="module")
def provider():
    return LocalEmbeddingProvider()


def test_provider_dimensions(provider):
    assert provider.dimensions == 384


def test_embedding_generation(provider):
    text = "Les politiques de sécurité doivent être définies et approuvées."

    embedding = provider.get_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(value, float) for value in embedding)


def test_embedding_is_normalized(provider):
    text = "Sécurité des systèmes d'information"

    embedding = np.array(
        provider.get_embedding(text),
        dtype=np.float32,
    )

    norm = np.linalg.norm(embedding)

    assert np.isclose(norm, 1.0, atol=1e-5)


def test_different_texts_produce_different_embeddings(provider):
    embedding_1 = provider.get_embedding(
        "Politiques de sécurité de l'information"
    )

    embedding_2 = provider.get_embedding(
        "Séparation des responsabilités administratives"
    )

    assert embedding_1 != embedding_2


def test_empty_text_is_rejected(provider):
    with pytest.raises(ValueError):
        provider.get_embedding("")