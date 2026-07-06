import ipaddress
from urllib.parse import urlparse

import tldextract

try:
    import validators
except ModuleNotFoundError:  # Allows the MVP to run in lean local environments.
    validators = None

SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "update",
    "secure",
    "account",
    "banking",
    "password",
    "wallet",
    "crypto",
    "payment",
    "invoice",
    "support",
    "unlock",
    "confirm",
}

URL_SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "ow.ly",
    "t.co",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
}

SUSPICIOUS_TLDS = {
    "zip",
    "mov",
    "top",
    "xyz",
    "click",
    "link",
    "work",
    "quest",
    "country",
    "stream",
    "gq",
    "tk",
}

MAX_SCORE = 100
LONG_URL_THRESHOLD = 120
SUBDOMAIN_THRESHOLD = 3
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


def _clamp_score(score: int) -> int:
    return max(0, min(score, MAX_SCORE))


def _is_ip_hostname(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _hostname(parsed_url) -> str:
    return (parsed_url.hostname or "").lower().strip(".")


def _is_valid_url(url: str) -> bool:
    if validators is not None:
        return bool(validators.url(url))

    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def analyze_url(url: str) -> dict[str, object]:
    """Score suspicious URL characteristics without making network calls."""

    score = 0
    reasons: list[str] = []
    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    hostname = _hostname(parsed)
    extracted = extract_domain(normalized_url)

    if not _is_valid_url(normalized_url):
        score += 20
        reasons.append("URL format is invalid or incomplete.")

    if parsed.scheme.lower() != "https":
        score += 18
        reasons.append("The URL does not use HTTPS.")

    if hostname and _is_ip_hostname(hostname):
        score += 25
        reasons.append("The URL uses an IP address instead of a domain name.")

    if len(normalized_url) > LONG_URL_THRESHOLD:
        score += 12
        reasons.append("The URL is unusually long.")

    registered_domain = ".".join(part for part in [extracted.domain, extracted.suffix] if part)
    if registered_domain in URL_SHORTENERS or hostname in URL_SHORTENERS:
        score += 22
        reasons.append("The URL uses a known URL shortener.")

    lower_url = normalized_url.lower()
    for keyword in sorted(SUSPICIOUS_KEYWORDS):
        if keyword in lower_url:
            score += 5
            reasons.append(f"The URL contains the suspicious keyword '{keyword}'.")

    if extracted.suffix.lower() in SUSPICIOUS_TLDS:
        score += 14
        reasons.append(f"The URL uses a suspicious top-level domain '.{extracted.suffix}'.")

    subdomain_parts = [part for part in extracted.subdomain.split(".") if part]
    if len(subdomain_parts) > SUBDOMAIN_THRESHOLD:
        score += 12
        reasons.append("The URL contains an excessive number of subdomains.")

    if not reasons:
        reasons.append("No obvious URL-level risk indicators were detected.")

    return {"score": _clamp_score(score), "reasons": reasons}
