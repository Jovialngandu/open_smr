from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.risk import AIAssessment, RiskAssessmentRequest


class GeminiProvider:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def assess(
        self,
        data: RiskAssessmentRequest,
    ) -> AIAssessment:
        prompt = f"""
Tu es un assistant d'analyse des risques informatiques.

Évalue le scénario en utilisant exclusivement les informations fournies.

ÉCHELLES :
- Vraisemblance : 1 (rare) à 5 (quasi certaine).
- Impact : 1 (mineur) à 5 (critique).

RÈGLES :
- Évalue le scénario décrit, pas une menace hypothétique différente.
- Utilise les valeurs de confidentialité, intégrité et disponibilité
  comme contexte, sans les convertir automatiquement en impact.
- N'invente ni contrôles de sécurité, ni incidents passés, ni fréquence.
- Si le contexte est insuffisant, indique cette limite dans la justification.
- La vraisemblance concerne la possibilité que l'incident se produise.
- L'impact concerne les conséquences si l'incident se produit.
- Fournis une justification courte en français.

ASSET :
{data.asset.model_dump_json(indent=2)}

SCÉNARIO DE MENACE :
{data.threat_description}
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIAssessment,
                temperature=0,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini a renvoyé une réponse vide.")

        return AIAssessment.model_validate_json(response.text)