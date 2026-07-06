from fastapi import APIRouter

from app.schemas.request import AuditRequest
from app.schemas.response import AuditResponse, CrooAuditResponse
from app.services.explanation import generate_explanation
from app.services.page_analyzer import analyze_page
from app.services.reputation import reputation_service
from app.services.risk_engine import calculate_risk
from app.services.url_analyzer import analyze_url

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.post("", response_model=AuditResponse)
@router.post("/", response_model=AuditResponse, include_in_schema=False)
def audit(request: AuditRequest) -> AuditResponse:
    """Run the complete deterministic audit pipeline for the active browser tab."""

    page_text = request.page_text or ""
    html = request.html or ""
    url_analysis = analyze_url(request.url)
    page_analysis = analyze_page(
        url=request.url,
        title=request.title,
        page_text=page_text,
        html=html,
    )
    reputation_analysis = reputation_service.analyze(request.url)
    risk_assessment = calculate_risk(url_analysis, page_analysis, reputation_analysis)
    explanation = generate_explanation(risk_assessment)
    reasons = [str(reason) for reason in risk_assessment["reasons"]]

    return AuditResponse(
        url=request.url,
        risk_score=int(risk_assessment["risk_score"]),
        risk_level=str(risk_assessment["risk_level"]),
        reasons=reasons,
        recommendation=str(risk_assessment["recommendation"]),
        explanation=explanation,
        evidence=reasons,
        croo=CrooAuditResponse(agent_used=False, response=None),
    )
