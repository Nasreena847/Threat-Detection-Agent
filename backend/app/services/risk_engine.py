AnalysisResult = dict[str, object]


def _score(result: AnalysisResult) -> int:
    return int(result.get("score", 0))


def _reasons(result: AnalysisResult) -> list[str]:
    reasons = result.get("reasons", [])
    return [str(reason) for reason in reasons] if isinstance(reasons, list) else []


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
) -> dict[str, object]:
    """Merge analyzer scores into a single user-facing risk assessment."""

    url_score = _score(url_analysis)
    page_score = _score(page_analysis)
    reputation_score = _score(reputation_analysis)
    max_component = max(url_score, page_score, reputation_score)
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

    risk_score = max(0, min(weighted_score, 100))
    reasons = (
        _reasons(url_analysis)
        + _reasons(page_analysis)
        + _reasons(reputation_analysis)
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
        },
        "threat_intel": {
            "provider": reputation_analysis.get("provider"),
            "virustotal": reputation_analysis.get("virustotal"),
        },
    }
