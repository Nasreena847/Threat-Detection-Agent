from pydantic import BaseModel, Field


class CrooAuditResponse(BaseModel):
    agent_used: bool = False
    response: dict[str, object] | None = None


class AuditResponse(BaseModel):
    scan_id: int | None = None
    url: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    reasons: list[str]
    recommendation: str
    explanation: str
    explanation_source: dict[str, object] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    ad_risk: dict[str, object] = Field(default_factory=dict)
    threat_intel: dict[str, object] = Field(default_factory=dict)
    ml: dict[str, object] = Field(default_factory=dict)
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


class ScanHistoryItem(BaseModel):
    id: int
    created_at: str
    url: str
    domain: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    explanation_source: str
    report: dict[str, object]


class ScanHistoryResponse(BaseModel):
    scans: list[ScanHistoryItem]
