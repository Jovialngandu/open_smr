from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseOIDCProvider(ABC):
    """Interface abstraite pour un fournisseur OIDC."""

    provider_name = 'base'

    @classmethod
    @abstractmethod
    def verify_id_token(cls, id_token: str) -> Dict[str, Any]:
        """Valide un token et retourne le payload standardisé."""
        raise NotImplementedError
