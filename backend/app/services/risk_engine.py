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

    weighted_score = round(
        (_score(url_analysis) * 0.35)
        + (_score(page_analysis) * 0.45)
        + (_score(reputation_analysis) * 0.20)
    )
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
            "url": _score(url_analysis),
            "page": _score(page_analysis),
            "reputation": _score(reputation_analysis),
        },
    }
