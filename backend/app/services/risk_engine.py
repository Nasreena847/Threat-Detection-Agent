AnalysisResult = dict[str, object]


def _score(result: AnalysisResult) -> int:
    return int(result.get("score", 0))


def _reasons(result: AnalysisResult) -> list[str]:
    reasons = result.get("reasons", [])
    return [str(reason) for reason in reasons] if isinstance(reasons, list) else []


def _has_trusted_reputation(reputation_analysis: AnalysisResult) -> bool:
    return any(
        "reputation appears trusted" in reason.lower() for reason in _reasons(reputation_analysis)
    )


def _ad_risk(page_analysis: AnalysisResult) -> dict[str, object]:
    ad_risk = page_analysis.get("ad_risk")
    return ad_risk if isinstance(ad_risk, dict) else {"count": 0, "score": 0, "severity": "none"}


def _risk_level(score: int) -> str:
    if score <= 25:
        return "Safe"
    if score <= 60:
        return "Medium"
    return "High"


def _recommendation(score: int) -> str:
    if score <= 25:
        return "The website appears safe based on the available signals."
    if score <= 60:
        return "Exercise caution and avoid sharing sensitive information unless you trust the site."
    return "Avoid interacting with this website and do not enter credentials or payment details."


def calculate_risk(
    url_analysis: AnalysisResult,
    page_analysis: AnalysisResult,
    reputation_analysis: AnalysisResult,
    ml_analysis: AnalysisResult | None = None,
) -> dict[str, object]:
    """Merge analyzer scores into a single user-facing risk assessment."""

    url_score = _score(url_analysis)
    page_score = _score(page_analysis)
    reputation_score = _score(reputation_analysis)
    ad_risk = _ad_risk(page_analysis)
    ad_risk_score = int(ad_risk.get("score") or 0)
    trusted_reputation = _has_trusted_reputation(reputation_analysis)
    ml_available = bool((ml_analysis or {}).get("available"))
    ml_score = _score(ml_analysis or {}) if ml_available else 0
    ml_has_rule_support = url_score >= 18 or page_score >= 18 or reputation_score >= 20
    if trusted_reputation and url_score <= 10 and reputation_score <= 10 and page_score < 50:
        ml_has_rule_support = False
    elif url_score <= 10 and reputation_score <= 10 and page_score < 25:
        ml_has_rule_support = False
    max_component = max(url_score, page_score, reputation_score, ml_score if ml_has_rule_support else 0)
    weighted_score = round(
        (url_score * 0.38)
        + (page_score * 0.47)
        + (reputation_score * 0.15)
    )

    if max_component >= 70:
        weighted_score = max(weighted_score, round(max_component * 0.72))
    elif max_component >= 45:
        weighted_score = max(weighted_score, round(max_component * 0.65))
    elif max_component >= 25:
        weighted_score = max(weighted_score, round(max_component * 0.55))

    if url_score >= 25 and page_score >= 25:
        weighted_score += 10
    elif url_score >= 18 and page_score >= 18:
        weighted_score += 6

    if ml_available and ml_score >= 50 and ml_has_rule_support:
        weighted_score = max(weighted_score, round((weighted_score * 0.72) + (ml_score * 0.28)))
    if ml_available and ml_score >= 80 and ml_has_rule_support:
        weighted_score = max(weighted_score, round(ml_score * 0.78))

    if trusted_reputation and url_score <= 10 and reputation_score <= 10:
        if page_score < 25:
            weighted_score = min(weighted_score, 12)
        elif page_score < 50:
            weighted_score = min(weighted_score, 24)
        elif page_score < 70:
            weighted_score = min(weighted_score, 38)

    if ad_risk_score >= 60:
        weighted_score = max(weighted_score, round(ad_risk_score * 0.9))
    elif ad_risk_score >= 50:
        weighted_score = max(weighted_score, 42)
    elif ad_risk_score >= 30:
        weighted_score = max(weighted_score, 28)
    elif ad_risk_score > 0:
        weighted_score = max(weighted_score, 16)

    risk_score = max(0, min(weighted_score, 100))
    ml_reasons = _reasons(ml_analysis or {}) if ml_available else []
    if ml_available and ml_score >= 50 and not ml_has_rule_support:
        ml_reasons = [
            "ML classifier produced an elevated phishing estimate, but the score was not raised because rule-based and reputation signals did not corroborate it."
        ]
    reasons = (
        _reasons(url_analysis)
        + _reasons(page_analysis)
        + _reasons(reputation_analysis)
        + ml_reasons
    )

    return {
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "reasons": reasons,
        "recommendation": _recommendation(risk_score),
        "components": {
            "url": url_score,
            "page": page_score,
            "reputation": reputation_score,
            "ml": ml_score,
            "ads": ad_risk_score,
        },
        "ad_risk": ad_risk,
        "threat_intel": {
            "provider": reputation_analysis.get("provider"),
            "dns": reputation_analysis.get("dns"),
            "virustotal": reputation_analysis.get("virustotal"),
        },
        "ml": {
            "available": ml_available,
            "score": ml_score,
            "probability": (ml_analysis or {}).get("probability"),
            "threshold": (ml_analysis or {}).get("threshold"),
            "verdict": (ml_analysis or {}).get("verdict"),
            "model_path": (ml_analysis or {}).get("model_path"),
            "feature_count": (ml_analysis or {}).get("feature_count"),
        },
    }
