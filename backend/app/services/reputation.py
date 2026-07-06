from urllib.parse import urlparse

import tldextract

KNOWN_TRUSTED_DOMAINS = {
    "google.com",
    "github.com",
    "microsoft.com",
    "apple.com",
    "amazon.com",
    "cloudflare.com",
    "wikipedia.org",
}

HIGH_RISK_TERMS = {
    "phish",
    "malware",
    "free-crypto",
    "airdrop",
    "wallet-verify",
    "account-restore",
}
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


class ReputationService:
    """Abstraction for domain reputation providers.

    The MVP uses a deterministic local score. A later implementation can replace
    this class with VirusTotal, Google Safe Browsing, or another provider while
    keeping the audit workflow unchanged.
    """

    def analyze(self, url: str) -> dict[str, object]:
        parsed = urlparse(url)
        extracted = extract_domain(url)
        registered_domain = ".".join(
            part for part in [extracted.domain, extracted.suffix] if part
        ).lower()
        normalized_url = url.lower()

        score = 8
        reasons: list[str] = ["Mock reputation check completed."]

        if registered_domain in KNOWN_TRUSTED_DOMAINS:
            return {
                "score": 0,
                "reasons": [f"Domain reputation appears trusted for {registered_domain}."],
                "provider": "mock",
            }

        for term in sorted(HIGH_RISK_TERMS):
            if term in normalized_url:
                score += 20
                reasons.append(f"Mock reputation found high-risk term '{term}' in the URL.")

        if parsed.hostname and parsed.hostname.count("-") >= 3:
            score += 10
            reasons.append("Domain contains multiple hyphens, a common phishing pattern.")

        return {"score": min(score, 100), "reasons": reasons, "provider": "mock"}


reputation_service = ReputationService()
