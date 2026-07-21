import ipaddress
import math
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

BRAND_DOMAINS = {
    "paypal": {"paypal.com"},
    "google": {"google.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com", "outlook.com"},
    "apple": {"apple.com"},
    "amazon": {"amazon.com"},
    "facebook": {"facebook.com", "meta.com"},
    "instagram": {"instagram.com"},
    "netflix": {"netflix.com"},
    "binance": {"binance.com"},
    "coinbase": {"coinbase.com"},
    "github": {"github.com"},
    "docusign": {"docusign.com"},
    "dropbox": {"dropbox.com"},
}

MAX_SCORE = 100
LONG_URL_THRESHOLD = 120
LONG_PATH_THRESHOLD = 70
SUBDOMAIN_THRESHOLD = 3
QUERY_PARAM_THRESHOLD = 6
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata",
    "metadata.google.internal",
}
BLOCKED_METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
}
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


def _clamp_score(score: int) -> int:
    return max(0, min(score, MAX_SCORE))


def _is_ip_hostname(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _parse_ip_hostname(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def _is_blocked_ip(ip_address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip_address in BLOCKED_METADATA_IPS
        or ip_address.is_loopback
        or ip_address.is_private
        or ip_address.is_link_local
        or ip_address.is_multicast
        or ip_address.is_reserved
        or ip_address.is_unspecified
    )


def _hostname(parsed_url) -> str:
    return (parsed_url.hostname or "").lower().strip(".")


def _registered_domain(extracted) -> str:
    return ".".join(part for part in [extracted.domain, extracted.suffix] if part).lower()


def _entropy(value: str) -> float:
    if not value:
        return 0.0

    counts = {character: value.count(character) for character in set(value)}
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _looks_random(label: str) -> bool:
    compact = "".join(character for character in label.lower() if character.isalnum())
    if len(compact) < 12:
        return False

    digit_ratio = sum(character.isdigit() for character in compact) / len(compact)
    return _entropy(compact) > 3.35 and digit_ratio > 0.15


def _is_valid_url(url: str) -> bool:
    if validators is not None:
        return bool(validators.url(url))

    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _port(parsed_url) -> int | None:
    try:
        return parsed_url.port
    except ValueError:
        return None


def validate_public_audit_url(url: str) -> None:
    """Reject URLs that should never be accepted by the public audit endpoint."""

    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    hostname = _hostname(parsed)

    if not _is_valid_url(normalized_url):
        raise ValueError("URL format is invalid or incomplete.")

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs can be audited.")

    if not hostname:
        raise ValueError("URL must include a hostname.")

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise ValueError("Localhost and metadata hostnames cannot be audited.")

    ip_address = _parse_ip_hostname(hostname)
    if ip_address is not None and _is_blocked_ip(ip_address):
        raise ValueError("Local, private, reserved, and cloud metadata IP addresses cannot be audited.")


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

    registered_domain = _registered_domain(extracted)
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

    if "@" in parsed.netloc:
        score += 25
        reasons.append("The URL uses '@' in the authority section, which can hide the real destination.")

    port = _port(parsed)
    if port and port not in {80, 443}:
        score += 10
        reasons.append(f"The URL uses a non-standard port ({port}).")

    path_and_query = f"{parsed.path}?{parsed.query}".strip("?")
    if len(path_and_query) > LONG_PATH_THRESHOLD:
        score += 8
        reasons.append("The URL path or query string is unusually long.")

    if parsed.query and parsed.query.count("&") + 1 > QUERY_PARAM_THRESHOLD:
        score += 8
        reasons.append("The URL contains an unusually large number of query parameters.")

    if "%" in lower_url:
        score += 7
        reasons.append("The URL contains encoded characters that can obscure the destination.")

    if "xn--" in hostname:
        score += 18
        reasons.append("The domain uses punycode, which can be used for lookalike domains.")

    domain_label = extracted.domain.lower()
    if domain_label.count("-") >= 2:
        score += 8
        reasons.append("The domain contains multiple hyphens, a common impersonation pattern.")

    if sum(character.isdigit() for character in domain_label) >= 3:
        score += 8
        reasons.append("The domain contains several digits, which can indicate automated or lookalike naming.")

    if _looks_random(domain_label):
        score += 14
        reasons.append("The domain label appears randomly generated.")

    for brand, official_domains in BRAND_DOMAINS.items():
        if brand in domain_label and registered_domain not in official_domains:
            score += 24
            reasons.append(f"The domain references '{brand}' but is not an official {brand} domain.")

    if not reasons:
        reasons.append("No obvious URL-level risk indicators were detected.")

    return {"score": _clamp_score(score), "reasons": reasons}
