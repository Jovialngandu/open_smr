from pydantic import BaseModel, Field


class AssetContext(BaseModel):
    name: str
    category: str
    description: str = ""
    confidentiality: int = Field(ge=1, le=3)
    integrity: int = Field(ge=1, le=3)
    availability: int = Field(ge=1, le=3)


class RiskAssessmentRequest(BaseModel):
    asset: AssetContext
    threat_description: str = Field(min_length=5, max_length=5000)


class AIAssessment(BaseModel):
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    justification: str


class RiskAssessmentResponse(AIAssessment):
    provider: str