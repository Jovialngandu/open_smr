from fastapi import APIRouter

from app.api.routes import health, risk_assessment

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(
    risk_assessment.router,
    tags=["Risk Assessment"],
)