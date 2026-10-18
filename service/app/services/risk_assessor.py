from app.core.config import settings
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from app.services.providers.gemini import GeminiProvider


class RiskAssessor:
    def __init__(self) -> None:
        self.provider = GeminiProvider()

    def assess(
        self,
        data: RiskAssessmentRequest,
    ) -> RiskAssessmentResponse:
        result = self.provider.assess(data)

        return RiskAssessmentResponse(
            **result.model_dump(),
            provider=f"gemini:{settings.gemini_model}",
        )


risk_assessor = RiskAssessor()