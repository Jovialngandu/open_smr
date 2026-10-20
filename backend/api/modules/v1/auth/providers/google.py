import json
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import urlopen

import jwt
from jwt import PyJWKSet
from django.conf import settings
from .base import BaseOIDCProvider


class GoogleOIDCProvider(BaseOIDCProvider):
    provider_name = 'google'
    JWKS_URL = 'https://www.googleapis.com/oauth2/v3/certs'
    ISSUERS = ('https://accounts.google.com', 'accounts.google.com')

    @classmethod
    def _fetch_jwks(cls) -> Dict[str, Any]:
        try:
            with urlopen(cls.JWKS_URL, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as exc:
            raise ValueError('Impossible de récupérer les clés Google JWKS.') from exc

    @classmethod
    def _get_signing_key(cls, token: str):
        jwks_data = cls._fetch_jwks()
        jwk_set = PyJWKSet.from_dict(jwks_data)
        
        # Extrait le header sans valider la signature
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        for jwk in jwk_set.keys:
            if jwk.key_id == kid:
                return jwk.key

        raise ValueError(f'Aucune clé de signature Google compatible trouvée pour kid: {kid}')

    @classmethod
    def verify_id_token(cls, id_token: str) -> Dict[str, Any]:
        if not id_token:
            raise ValueError('Le champ id_token est obligatoire.')

        client_id = getattr(settings, 'GOOGLE_OIDC_CLIENT_ID', None)
        if not client_id:
            raise ValueError('GOOGLE_OIDC_CLIENT_ID n’est pas configuré dans settings.')

        try:
            signing_key = cls._get_signing_key(id_token)
            
            claims = jwt.decode(
                id_token,
                key=signing_key,
                algorithms=['RS256'],
                audience=client_id,
                issuer=cls.ISSUERS,
                options={'require': ['exp', 'iss', 'aud', 'sub', 'email']},
            )
        except Exception as exc:
            raise ValueError(f'Jeton Google OIDC invalide ou expiré ({exc}).') from exc

        if claims.get('email_verified') is False:
            raise ValueError('Le compte Google n’a pas une adresse e-mail vérifiée.')

        return {
            'email': claims.get('email', '').strip().lower(),
            'first_name': claims.get('given_name', '').strip(),
            'last_name': claims.get('family_name', '').strip(),
            'sub': str(claims.get('sub', '')),
            'provider': 'google',
        }