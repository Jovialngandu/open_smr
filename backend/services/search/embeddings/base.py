from abc import ABC, abstractmethod

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> list:
        """Méthode obligatoire que chaque provider doit implémenter."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Renvoie le nombre de dimensions du modèle (ex: 384 ou 1536)."""
        pass
