from typing import Dict, Type

from .providers.base import BaseOIDCProvider
from .providers.google import GoogleOIDCProvider


class OIDCBackend:
    """Orchestrateur central réutilisable pour la validation des fournisseurs OIDC."""

    providers: Dict[str, Type[BaseOIDCProvider]] = {
        'google': GoogleOIDCProvider,
    }

    @classmethod
    def get_provider(cls, provider: str) -> Type[BaseOIDCProvider]:
        provider_name = (provider or 'google').lower()
        if provider_name not in cls.providers:
            raise ValueError(f'Fournisseur OIDC inconnu: {provider}')
        return cls.providers[provider_name]

    @classmethod
    def authenticate(cls, *, id_token: str, provider: str = 'google') -> Dict[str, str]:
        provider_cls = cls.get_provider(provider)

        return provider_cls.verify_id_token(id_token)


GoogleOIDCProvider = GoogleOIDCProvider
