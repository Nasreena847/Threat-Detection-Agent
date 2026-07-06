from pydantic import BaseModel, Field


class CrooAuditResponse(BaseModel):
    agent_used: bool = False
    response: dict[str, object] | None = None


class AuditResponse(BaseModel):
    url: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    reasons: list[str]
    recommendation: str
    explanation: str
    evidence: list[str] = Field(default_factory=list)
    croo: CrooAuditResponse = Field(default_factory=CrooAuditResponse)


class CrooAgent(BaseModel):
    id: str
    name: str
    description: str
    available: bool


class CrooAgentsResponse(BaseModel):
    agents: list[CrooAgent]


class CrooInvokeResponse(BaseModel):
    agent_id: str
    invoked: bool
    response: dict[str, object]
