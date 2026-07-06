def generate_explanation(risk_result: dict[str, object]) -> str:
    """Create a deterministic natural-language explanation for the audit result."""

    risk_score = int(risk_result["risk_score"])
    risk_level = str(risk_result["risk_level"])
    recommendation = str(risk_result["recommendation"])
    reasons = [str(reason) for reason in risk_result.get("reasons", [])]
    signal_count = len(reasons)

    if risk_level == "Safe":
        return (
            f"This site is classified as Safe with a risk score of {risk_score}. "
            "The agent did not identify strong phishing or malware indicators in the "
            "submitted URL and page metadata. "
            f"Recommendation: {recommendation}"
        )

    leading_reasons = "; ".join(reasons[:3]) if reasons else "risk indicators were detected"
    return (
        f"This site is classified as {risk_level} risk with a risk score of {risk_score}. "
        f"The assessment found {signal_count} indicator(s), including: {leading_reasons}. "
        f"Recommendation: {recommendation}"
    )
