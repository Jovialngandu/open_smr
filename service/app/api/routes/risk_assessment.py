from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_service_key
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from app.services.risk_assessor import risk_assessor

router = APIRouter(
    dependencies=[Depends(require_service_key)]
)


@router.post(
    "/assess-risk",
    response_model=RiskAssessmentResponse,
)
def assess_risk(
    data: RiskAssessmentRequest,
) -> RiskAssessmentResponse:
    try:
        return risk_assessor.assess(data)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Échec de l'évaluation du risque"
        )
        raise HTTPException(
            status_code=502,
            detail="Le service d'évaluation IA est indisponible.",
        ) from exc