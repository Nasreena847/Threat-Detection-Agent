from app.services.llm_explanation import llm_explanation_service
from app.services.ml_classifier import ml_classifier_service
from app.services.page_analyzer import analyze_page
from app.services.reputation import reputation_service
from app.services.risk_engine import calculate_risk
from app.services.url_analyzer import analyze_url, validate_public_audit_url


def run_audit_pipeline(
    url: str,
    title: str = "",
    page_text: str = "",
    html: str = "",
    forms: int | None = None,
    scripts: int | None = None,
    password_fields: int | None = None,
    iframes: int | None = None,
) -> dict[str, object]:
    """Run the shared deterministic audit pipeline used by both the audit route and CROO integration."""

    validate_public_audit_url(url)
    url_analysis = analyze_url(url)
    page_analysis = analyze_page(
        url=url,
        title=title,
        page_text=page_text,
        html=html,
        forms=forms,
        scripts=scripts,
        password_fields=password_fields,
        iframes=iframes,
    )
    reputation_analysis = reputation_service.analyze(url)
    ml_analysis = ml_classifier_service.analyze(url)
    risk_assessment = calculate_risk(url_analysis, page_analysis, reputation_analysis, ml_analysis)
    explanation_result = llm_explanation_service.generate(risk_assessment)
    reasons = [str(reason) for reason in risk_assessment["reasons"]]

    return {
        "url": url,
        "risk_score": int(risk_assessment["risk_score"]),
        "risk_level": str(risk_assessment["risk_level"]),
        "reasons": reasons,
        "recommendation": str(explanation_result["recommendation"]),
        "explanation": str(explanation_result["explanation"]),
        "explanation_source": explanation_result,
        "components": risk_assessment.get("components", {}),
        "threat_intel": risk_assessment.get("threat_intel", {}),
        "ml": risk_assessment.get("ml", {}),
    }
