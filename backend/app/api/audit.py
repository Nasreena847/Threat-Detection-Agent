from fastapi import APIRouter

from app.schemas.request import AuditRequest
from app.schemas.response import AuditResponse, CrooAuditResponse
from app.services.audit_pipeline import run_audit_pipeline

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.post("", response_model=AuditResponse)
@router.post("/", response_model=AuditResponse, include_in_schema=False)
def audit(request: AuditRequest) -> AuditResponse:
    """Run the complete deterministic audit pipeline for the active browser tab."""

    result = run_audit_pipeline(
        url=request.url,
        title=request.title,
        page_text=request.page_text or "",
        html=request.html or "",
    )

    return AuditResponse(
        url=str(result["url"]),
        risk_score=int(result["risk_score"]),
        risk_level=str(result["risk_level"]),
        reasons=[str(reason) for reason in result["reasons"]],
        recommendation=str(result["recommendation"]),
        explanation=str(result["explanation"]),
        evidence=[str(reason) for reason in result["reasons"]],
        croo=CrooAuditResponse(agent_used=False, response=None),
    )
