import httpx

from django.conf import settings


class AIServiceError(Exception):
    """Erreur lors de l'appel au service IA."""


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
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

        # Validation minimale de la réponse distante.
        for field in ("likelihood", "impact"):
            value = result.get(field)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 1 <= value <= 5
            ):
                raise AIServiceError(
                    f"Valeur invalide reçue pour {field}."
                )

        if not isinstance(result.get("justification"), str):
            raise AIServiceError("Justification IA invalide.")

        return result

    except httpx.HTTPError as exc:
        raise AIServiceError(
            "Le service IA est indisponible."
        ) from exc