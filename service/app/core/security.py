import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings


api_key_header = APIKeyHeader(
    name="X-Service-Key",
    auto_error=False,
)


def require_service_key(
    api_key: str | None = Security(api_key_header),
) -> None:
    if not api_key or not secrets.compare_digest(
        api_key,
        settings.service_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification invalide.",
        )