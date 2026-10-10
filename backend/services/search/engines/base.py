from abc import ABC, abstractmethod

class BaseSearchEngine(ABC):
    @abstractmethod
    def search(self, query_text: str, top_k: int = 5) -> list:
        """Exécute la recherche et retourne une liste de résultats annotés."""
        pass
