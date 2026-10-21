import httpx

from django.conf import settings


class AIServiceError(Exception):
    """Erreur lors de l'appel au service IA."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _raise_for_http_status(response: httpx.Response) -> None:
    if response.status_code == 200:
        return
    if response.status_code == 429:
        raise AIServiceError(
            "Trop de demandes pour le service IA.",
            status_code=429,
        )
    if response.status_code in {408, 500, 502, 503, 504}:
        raise AIServiceError(
            "Le service IA est momentanément indisponible.",
            status_code=503,
        )
    if response.status_code in {400, 422}:
        raise AIServiceError(
            "La demande envoyée au service IA est invalide.",
            status_code=400,
        )
    if response.status_code in {401, 403}:
        raise AIServiceError(
            "Le service IA n'est pas configuré correctement.",
            status_code=500,
        )
    raise AIServiceError(
        "Le service IA est actuellement indisponible.",
        status_code=503,
    )


def chat(message: str, history=None, context: str = "") -> dict:
    payload = {
        "message": message,
        "history": history or [],
        "context": context or "",
    }

    try:
        response = httpx.post(
            f"{settings.AI_SERVICE_URL.rstrip('/')}/chat",
            json=payload,
            headers={
                "X-Service-Key": settings.AI_SERVICE_API_KEY,
            },
            timeout=settings.AI_SERVICE_CHAT_TIMEOUT,
        )
        _raise_for_http_status(response)
        result = response.json()
    except httpx.TimeoutException as exc:
        raise AIServiceError(
            "Le service IA n'a pas répondu à temps.",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise AIServiceError(
            "Le service IA est actuellement indisponible.",
            status_code=503,
        ) from exc
    except ValueError as exc:
        raise AIServiceError(
            "La réponse du service IA est invalide.",
            status_code=502,
        ) from exc

    if not isinstance(result.get("reply"), str) or not result["reply"].strip():
        raise AIServiceError(
            "La réponse du service IA est vide.",
            status_code=502,
        )

    return {"reply": result["reply"].strip()}


def assess_risk(asset, threat_description: str) -> dict:
    payload = {
        "asset": {
            "name": asset.name,
            "category": asset.category,
            "description": asset.description or "",
            "confidentiality": asset.confidentiality,
            "integrity": asset.integrity,
            "availability": asset.availability,
        },
        "threat_description": threat_description,
    }

    try:
        response = httpx.post(
            f"{settings.AI_SERVICE_URL.rstrip('/')}/assess-risk",
            json=payload,
            headers={
                "X-Service-Key": settings.AI_SERVICE_API_KEY,
            },
            timeout=settings.AI_SERVICE_RISK_TIMEOUT,
        )
        _raise_for_http_status(response)
        result = response.json()

        for field in ("likelihood", "impact"):
            value = result.get(field)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 1 <= value <= 5
            ):
                raise AIServiceError(
                    f"Valeur invalide reçue pour {field}.",
                    status_code=502,
                )

        if not isinstance(result.get("justification"), str):
            raise AIServiceError("Justification IA invalide.", status_code=502)

        return result

    except AIServiceError:
        raise
    except httpx.TimeoutException as exc:
        raise AIServiceError(
            "Le service IA n'a pas répondu à temps.",
            status_code=504,
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise AIServiceError(
            "Le service IA est indisponible.",
            status_code=503,
        ) from exc