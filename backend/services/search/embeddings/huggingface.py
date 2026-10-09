import requests

from django.conf import settings

from  services.search.embeddings.base import BaseEmbeddingProvider


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):

    def __init__(self):
        self.api_url = (
            "https://router.huggingface.co/hf-inference/models/"
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json",
        }

    def get_embedding(self, text: str) -> list:
        payload = {
            "inputs": text.strip(),
            "options": {
                "wait_for_model": True
            }
        }

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=60,
        )

        if response.status_code != 200:
            raise Exception(
                f"Erreur Hugging Face API "
                f"({response.status_code}): {response.text}"
            )

        data = response.json()

        if isinstance(data, list) and data:
            # [[0.1, 0.2, ...]]
            if isinstance(data[0], list):
                return data[0]

            # [0.1, 0.2, ...]
            return data

        raise Exception(
            f"Structure de données reçue invalide : {type(data)}"
        )

    @property
    def dimensions(self) -> int:
        return 384